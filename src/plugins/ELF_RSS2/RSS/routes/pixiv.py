import re

from .Parsing import ParsingBase
from ..rss_class import Rss


# 处理来源
@ParsingBase.append_handler(parsing_type="source", rex="pixiv", priority=10, block=True)
async def handle_source(
    rss: Rss, state: dict, item: dict, item_msg: str, tmp: str, tmp_state: dict
) -> str:
    source = item["link"]
    # 缩短 pixiv 链接
    str_link = re.sub("https://www.pixiv.net/artworks/", "https://pixiv.net/i/", source)
    return "链接：" + str_link + "\n"
