import httpx
import sqlite3

from nonebot import logger
from pyquery import PyQuery as Pq
from tenacity import retry, stop_after_attempt, stop_after_delay, RetryError

from .Parsing import (
    ParsingBase,
    get_proxy,
    write_item,
    cache_db_manage,
    duplicate_exists,
)
from .Parsing.handle_images import handle_img_combo
from ..rss_class import Rss
from ...config import DATA_PATH


# 处理图片
@ParsingBase.append_handler(parsing_type="picture", rex="danbooru")
async def handle_picture(
    rss: Rss, state: dict, item: dict, item_msg: str, tmp: str, tmp_state: dict
) -> str:

    # 判断是否开启了只推送标题
    if rss.only_title:
        return ""

    try:
        res = await handle_img(
            url=item["link"],
            img_proxy=rss.img_proxy,
        )
    except RetryError:
        res = "预览图获取失败"
        logger.error(f"[{item['link']}]的预览图获取失败")

    # 判断是否开启了只推送图片
    if rss.only_pic:
        return f"{res}\n"

    return f"{tmp + res}\n"


# 处理图片、视频
@retry(stop=(stop_after_attempt(5) | stop_after_delay(30)))
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


# 如果启用了去重模式，对推送列表进行过滤
@ParsingBase.append_before_handler(rex="danbooru", priority=12)
async def handle_check_update(rss: Rss, state: dict):
    change_data = state.get("change_data")
    conn = state.get("conn")
    db = state.get("tinydb")

    # 检查是否启用去重 使用 duplicate_filter_mode 字段
    if not rss.duplicate_filter_mode:
        return {"change_data": change_data}

    if not conn:
        conn = sqlite3.connect(DATA_PATH / "cache.db")
        conn.set_trace_callback(logger.debug)

    await cache_db_manage(conn)

    delete = []
    for index, item in enumerate(change_data):
        try:
            summary = await get_summary(item, rss.img_proxy)
        except RetryError:
            logger.error(f"[{item['link']}]的预览图获取失败")
            continue
        is_duplicate, image_hash = await duplicate_exists(
            rss=rss,
            conn=conn,
            link=item["link"],
            title=item["title"],
            summary=summary,
        )
        if is_duplicate:
            write_item(db, item)
            delete.append(index)
        else:
            change_data[index]["image_hash"] = str(image_hash)

    change_data = [
        item for index, item in enumerate(change_data) if index not in delete
    ]

    return {
        "change_data": change_data,
        "conn": conn,
    }


# 获取正文
@retry(stop=(stop_after_attempt(5) | stop_after_delay(30)))
async def get_summary(item: dict, img_proxy: bool) -> str:
    summary = (
        item["content"][0].get("value") if item.get("content") else item["summary"]
    )
    # 如果图片非视频封面，替换为更清晰的预览图
    summary_doc = Pq(summary)
    async with httpx.AsyncClient(proxies=get_proxy(img_proxy)) as client:
        response = await client.get(item["link"])
        d = Pq(response.text)
        img = d("img#image")
        if img:
            summary_doc("img").attr("src", img.attr("src"))
    return str(summary_doc)
