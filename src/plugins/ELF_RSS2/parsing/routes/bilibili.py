import re
from typing import Any, Dict

from nonebot.log import logger
from pyquery import PyQuery as Pq

from ...rss_class import Rss
from .. import ParsingBase, handle_html_tag
from ..utils import get_author, get_summary


# 处理正文 处理网页 tag
@ParsingBase.append_handler(parsing_type="summary", rex="/bilibili/")
async def handle_summary(rss: Rss, item: Dict[str, Any], tmp: str) -> str:
    try:
        tmp += handle_html_tag(html=Pq(get_summary(item)))
    except Exception as e:
        logger.warning(f"{rss.name} 没有正文内容！{e}")

    if author := get_author(item):
        author = f"UP 主： {author}"

    if "AuthorID:" in tmp:
        author_id = re.search(r"\nAuthorID: (\d+)", tmp)[1]  # type: ignore
        tmp = re.sub(r"\nAuthorID: \d+", "", tmp)
        tmp = f"{author}\nUP 主 ID： {author_id}\n{tmp}"
        tmp = (
            tmp.replace("Length:", "时长：")
            .replace("Play:", "播放量：")
            .replace("Favorite:", "收藏量：")
            .replace("Danmaku:", "弹幕数：")
            .replace("Comment:", "评论数：")
            .replace("Match By:", "匹配条件：")
        )
        return tmp

    return f"{author}\n{tmp}"
