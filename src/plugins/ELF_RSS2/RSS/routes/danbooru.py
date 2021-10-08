import httpx

from pyquery import PyQuery as Pq

from .Parsing import ParsingBase, get_proxy
from .Parsing.handle_images import handle_img_combo
from ..rss_class import Rss


# 处理图片
@ParsingBase.append_handler(parsing_type="picture", rex="danbooru")
async def handle_picture(
    rss: Rss, state: dict, item: dict, item_msg: str, tmp: str, tmp_state: dict
) -> str:

    # 判断是否开启了只推送标题
    if rss.only_title:
        return ""

    res = await handle_img(
        url=item["link"],
        img_proxy=rss.img_proxy,
    )

    # 判断是否开启了只推送图片
    if rss.only_pic:
        return f"{res}\n"

    return f"{tmp + res}\n"


# 处理图片、视频
async def handle_img(url: str, img_proxy: bool) -> str:
    img_str = ""

    # 处理图片
    async with httpx.AsyncClient(proxies=get_proxy(img_proxy)) as client:
        response = await client.get(url)
        d = Pq(response.text)
        img = d("img#image")
        if img:
            url = img.attr("src")
        else:
            img_str += "视频封面："
            url = d("meta[property='og:image']").attr("content")
        img_str += await handle_img_combo(url, img_proxy)

    return img_str
