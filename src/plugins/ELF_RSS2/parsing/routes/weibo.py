from typing import Any, Dict

from nonebot.log import logger
from pyquery import PyQuery as Pq

from ...config import config
from ...rss_class import Rss
from .. import ParsingBase, handle_html_tag
from ..handle_images import handle_img_combo, handle_img_combo_with_content
from ..utils import get_summary


# 处理正文 处理网页 tag
@ParsingBase.append_handler(parsing_type="summary", rex="/weibo/")
async def handle_summary(item: Dict[str, Any], tmp: str) -> str:
    summary_html = Pq(get_summary(item))

    # 判断是否保留转发内容
    if not config.blockquote:
        summary_html.remove("blockquote")

    tmp += handle_html_tag(html=summary_html)

    return tmp


# 处理图片
@ParsingBase.append_handler(parsing_type="picture", rex="/weibo/")
async def handle_picture(rss: Rss, item: Dict[str, Any], tmp: str) -> str:
    # 判断是否开启了只推送标题
    if rss.only_title:
        return ""

    res = ""
    try:
        res += await handle_img(
            item=item,
            img_proxy=rss.img_proxy,
            img_num=rss.max_image_number,
        )
    except Exception as e:
        logger.warning(f"{rss.name} 没有正文内容！{e}")

    # 判断是否开启了只推送图片
    return f"{res}\n" if rss.only_pic else f"{tmp + res}\n"


# 处理图片、视频
async def handle_img(item: Dict[str, Any], img_proxy: bool, img_num: int) -> str:
    if item.get("image_content"):
        return await handle_img_combo_with_content(
            item.get("gif_url", ""), item["image_content"]
        )
    html = Pq(get_summary(item))
    # 移除多余图标
    html.remove("span.url-icon")
    img_str = ""
    # 处理图片
    doc_img = list(html("img").items())
    # 只发送限定数量的图片，防止刷屏
    if 0 < img_num < len(doc_img):
        img_str += f"\n因启用图片数量限制，目前只有 {img_num} 张图片："
        doc_img = doc_img[:img_num]
    for img in doc_img:
        url = img.attr("src")
        img_str += await handle_img_combo(url, img_proxy)

    # 处理视频
    if doc_video := html("video"):
        img_str += "\n视频封面："
        for video in doc_video.items():
            url = video.attr("poster")
            img_str += await handle_img_combo(url, img_proxy)

    return img_str
