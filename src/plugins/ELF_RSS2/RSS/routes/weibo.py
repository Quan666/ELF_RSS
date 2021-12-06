from pyquery import PyQuery as Pq

from ...config import config
from ..rss_class import Rss
from .Parsing import ParsingBase, get_summary, handle_html_tag


# 处理正文 处理网页 tag
@ParsingBase.append_handler(parsing_type="summary", rex="weibo", priority=10)
async def handle_summary(
    rss: Rss, state: dict, item: dict, item_msg: str, tmp: str, tmp_state: dict
) -> str:
    summary_html = Pq(get_summary(item))

    # 判断是否保留转发内容
    if not config.blockquote:
        summary_html.remove("blockquote")

    tmp += await handle_html_tag(html=summary_html)

    return tmp
