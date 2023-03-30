from typing import Any, Dict

from ...rss_class import Rss
from .. import ParsingBase
from ..handle_images import handle_img_combo


# 处理图片
@ParsingBase.append_handler(
    parsing_type="picture",
    rex=r"https:\/\/www\.youtube\.com\/feeds\/videos\.xml\?channel_id=",
)
async def handle_picture(rss: Rss, item: Dict[str, Any], tmp: str) -> str:
    # 判断是否开启了只推送标题
    if rss.only_title:
        return ""

    img_url = item["media_thumbnail"][0]["url"]
    res = await handle_img_combo(img_url, rss.img_proxy)

    # 判断是否开启了只推送图片
    return f"{res}\n" if rss.only_pic else f"{tmp + res}\n"
