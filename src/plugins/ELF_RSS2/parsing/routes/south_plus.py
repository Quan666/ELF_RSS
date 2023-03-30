import re
from typing import Any, Dict

from nonebot.log import logger
from pyquery import PyQuery as Pq

from ...rss_class import Rss
from .. import ParsingBase, handle_html_tag
from ..handle_html_tag import handle_bbcode
from ..handle_images import handle_bbcode_img
from ..utils import get_summary


# 处理正文 处理网页 tag
@ParsingBase.append_handler(parsing_type="summary", rex="(south|spring)-plus.net")
async def handle_summary(item: Dict[str, Any], tmp: str) -> str:
    rss_str = handle_bbcode(html=Pq(get_summary(item)))
    tmp += handle_html_tag(html=Pq(rss_str))
    return tmp


# 处理图片
@ParsingBase.append_handler(parsing_type="picture", rex="(south|spring)-plus.net")
async def handle_picture(rss: Rss, item: Dict[str, Any], tmp: str) -> str:
    # 判断是否开启了只推送标题
    if rss.only_title:
        return ""

    res = ""
    try:
        res += await handle_bbcode_img(
            html=Pq(get_summary(item)),
            img_proxy=rss.img_proxy,
            img_num=rss.max_image_number,
        )
    except Exception as e:
        logger.warning(f"{rss.name} 没有正文内容！{e}")

    # 判断是否开启了只推送图片
    return f"{res}\n" if rss.only_pic else f"{tmp + res}\n"


# 处理来源
@ParsingBase.append_handler(parsing_type="source", rex="(south|spring)-plus.net")
async def handle_source(item: Dict[str, Any]) -> str:
    source = item["link"]
    # issue 36 处理链接
    if re.search(r"^//", source):
        source = source.replace("//", "https://")
    return f"链接：{source}\n"
