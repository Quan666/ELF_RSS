# 处理来源
import re

from .Parsing import ParsingBase


@ParsingBase.append_handler(parsing_type="source", rex="pixiv")
async def handle_source(source: str) -> str:
    # 缩短 pixiv 链接
    str_link = re.sub("https://www.pixiv.net/artworks/", "https://pixiv.net/i/", source)
    return f"链接：{str_link}\n"
