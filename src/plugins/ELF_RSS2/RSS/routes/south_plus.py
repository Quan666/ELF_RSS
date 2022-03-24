import re
from typing import Any, Dict

from nonebot.log import logger
from pyquery import PyQuery as Pq

from ..rss_class import Rss
from .Parsing import ParsingBase, get_summary, handle_bbcode, handle_html_tag
from .Parsing.handle_images import handle_bbcode_img


# 处理正文 处理网页 tag
@ParsingBase.append_handler(
    parsing_type="summary", rex="(south|spring)-plus.net", priority=10
)
async def handle_summary(
    rss: Rss,
    state: Dict[str, Any],
    item: Dict[str, Any],
    item_msg: str,
    tmp: str,
    tmp_state: Dict[str, Any],
) -> str:
    rss_str = await handle_bbcode(html=Pq(get_summary(item)))
    tmp += await handle_html_tag(html=Pq(rss_str))
    return tmp


# 处理图片
@ParsingBase.append_handler(parsing_type="picture", rex="(south|spring)-plus.net")
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
    if rss.only_pic:
        return f"{res}\n"

    return f"{tmp + res}\n"


# 处理来源
@ParsingBase.append_handler(parsing_type="source", rex="(south|spring)-plus.net")
async def handle_source(
    rss: Rss,
    state: Dict[str, Any],
    item: Dict[str, Any],
    item_msg: str,
    tmp: str,
    tmp_state: Dict[str, Any],
) -> str:
    source = item["link"]
    # issue 36 处理链接
    if re.search(r"^//", source):
        source = source.replace("//", "https://")
    return f"链接：{source}\n"
