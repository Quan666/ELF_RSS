# 处理来源
import re

from .Parsing import get_summary
from .Parsing import handle_html_tag
from .Parsing import ParsingBase
from ..rss_class import Rss
from pyquery import PyQuery as Pq


# 处理正文 处理网页 tag
@ParsingBase.append_handler(parsing_type="summary", priority=10)
async def handle_summary(rss: Rss, state: dict, item: dict, item_msg: str, tmp: str, tmp_state: dict) -> str:
    return await handle_html_tag(html=Pq(get_summary(item)))


@ParsingBase.append_handler(parsing_type="source", rex="south-plus", priority=10, block=True)
async def handle_source(rss: Rss, state: dict, item: dict, item_msg: str, tmp: str, tmp_state: dict) -> str:
    source = item["link"]
    # issue 36 处理链接
    if re.search(r"^//", source):
        source = source.replace("//", "https://")
    return "链接：" + source + "\n"
