from pyquery import PyQuery as Pq

from .Parsing import ParsingBase, get_summary, handle_html_tag
from ..rss_class import Rss
from ...config import config


# 处理正文 处理网页 tag
@ParsingBase.append_handler(parsing_type="summary", rex="weibo", priority=10)
async def handle_summary(
    rss: Rss, state: dict, item: dict, item_msg: str, tmp: str, tmp_state: dict
) -> str:
    summary_html = Pq(get_summary(item))

    # 判断是否保留转发内容，保留的话只去掉标签，留下里面的内容
    if config.blockquote:
        for blockquote in summary_html("blockquote").items():
            blockquote.replace_with(blockquote.html())
    else:
        summary_html.remove("blockquote")

    tmp += await handle_html_tag(html=summary_html)

    return tmp
