from typing import Any, Dict

from ..rss_class import Rss
from .Parsing import ParsingBase
from .Parsing.handle_images import handle_img_combo


# 处理图片
@ParsingBase.append_handler(
    parsing_type="picture",
    rex=r"https:\/\/www\.youtube\.com\/feeds\/videos\.xml\?channel_id=",
)
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

    img_url = item["media_thumbnail"][0]["url"]
    res = await handle_img_combo(img_url, rss.img_proxy)

    # 判断是否开启了只推送图片
    if rss.only_pic:
        return f"{res}\n"

    return f"{tmp + res}\n"
