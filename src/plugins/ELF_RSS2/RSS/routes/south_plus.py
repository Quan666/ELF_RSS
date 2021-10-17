import re

from pyquery import PyQuery as Pq

from .Parsing import ParsingBase, get_summary, handle_bbcode, handle_html_tag
from ..rss_class import Rss


# 处理正文 处理网页 tag
@ParsingBase.append_handler(
    parsing_type="summary", rex="(south|spring)-plus.net", priority=10
)
async def handle_summary(
    rss: Rss, state: dict, item: dict, item_msg: str, tmp: str, tmp_state: dict
) -> str:
    rss_str = await handle_bbcode(html=Pq(get_summary(item)))
    tmp += await handle_html_tag(html=Pq(rss_str))
    return tmp


# 处理来源
@ParsingBase.append_handler(parsing_type="source", rex="(south|spring)-plus.net")
async def handle_source(
    rss: Rss, state: dict, item: dict, item_msg: str, tmp: str, tmp_state: dict
) -> str:
    source = item["link"]
    # issue 36 处理链接
    if re.search(r"^//", source):
        source = source.replace("//", "https://")
    return "链接：" + source + "\n"
