from typing import Any, Dict

from nonebot.log import logger
from pyquery import PyQuery as Pq
from tenacity import RetryError

from ...rss_class import Rss
from .. import ParsingBase
from ..handle_images import (
    get_preview_gif_from_video,
    handle_img_combo,
    handle_img_combo_with_content,
)
from ..utils import get_summary


# 处理图片
@ParsingBase.append_handler(parsing_type="picture", rex="twitter")
async def handle_picture(
    rss: Rss,
    state: Dict[str, Any],
    item: Dict[str, Any],
    item_msg: str,
    tmp: str,
    tmp_state: Dict[str, Any],
) -> str:

    # 判断是否开启了只推送标题
    if rss.only_title:
        return ""

    res = await handle_img(
        item=item,
        img_proxy=rss.img_proxy,
        img_num=rss.max_image_number,
    )

    # 判断是否开启了只推送图片
    if rss.only_pic:
        return f"{res}\n"

    return f"{tmp + res}\n"


# 处理图片、视频
async def handle_img(item: Dict[str, Any], img_proxy: bool, img_num: int) -> str:
    if item.get("image_content"):
        return await handle_img_combo_with_content(
            item.get("gif_url", ""), item["image_content"]
        )
    html = Pq(get_summary(item))
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
        img_str += "\n视频预览："
        for video in doc_video.items():
            url = video.attr("src")
            try:
                url = await get_preview_gif_from_video(url)
            except RetryError:
                logger.warning("视频预览获取失败，将发送原视频封面")
                url = video.attr("poster")
            img_str += await handle_img_combo(url, img_proxy)

    return img_str
