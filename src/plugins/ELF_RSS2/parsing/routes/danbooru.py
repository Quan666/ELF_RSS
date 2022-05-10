import sqlite3
from typing import Any, Dict

import aiohttp
from nonebot.log import logger
from pyquery import PyQuery as Pq
from tenacity import RetryError, retry, stop_after_attempt, stop_after_delay

from ...config import DATA_PATH
from ...rss_class import Rss
from .. import ParsingBase, cache_db_manage, duplicate_exists, write_item
from ..handle_images import (
    get_preview_gif_from_video,
    handle_img_combo,
    handle_img_combo_with_content,
)
from ..utils import get_proxy


# 处理图片
@ParsingBase.append_handler(parsing_type="picture", rex="danbooru")
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

    try:
        res = await handle_img(
            item=item,
            img_proxy=rss.img_proxy,
        )
    except RetryError:
        res = "预览图获取失败"
        logger.warning(f"[{item['link']}]的预览图获取失败")

    # 判断是否开启了只推送图片
    if rss.only_pic:
        return f"{res}\n"

    return f"{tmp + res}\n"


# 处理图片、视频
@retry(stop=(stop_after_attempt(5) | stop_after_delay(30)))  # type: ignore
async def handle_img(item: Dict[str, Any], img_proxy: bool) -> str:
    if item.get("image_content"):
        return await handle_img_combo_with_content(
            item.get("gif_url", ""), item["image_content"]
        )
    img_str = ""

    # 处理图片
    async with aiohttp.ClientSession() as session:
        resp = await session.get(item["link"], proxy=get_proxy(img_proxy))
        d = Pq(await resp.text())
        if img := d("img#image"):
            url = img.attr("src")
        else:
            img_str += "视频预览："
            url = d("video#image").attr("src")
            try:
                url = await get_preview_gif_from_video(url)
            except RetryError:
                logger.warning("视频预览获取失败，将发送原视频封面")
                url = d("meta[property='og:image']").attr("content")
        img_str += await handle_img_combo(url, img_proxy)

    return img_str


# 如果启用了去重模式，对推送列表进行过滤
@ParsingBase.append_before_handler(rex="danbooru", priority=12)
async def handle_check_update(rss: Rss, state: Dict[str, Any]) -> Dict[str, Any]:
    change_data = state["change_data"]
    conn = state["conn"]
    db = state["tinydb"]

    # 检查是否启用去重 使用 duplicate_filter_mode 字段
    if not rss.duplicate_filter_mode:
        return {"change_data": change_data}

    if not conn:
        conn = sqlite3.connect(str(DATA_PATH / "cache.db"))
        conn.set_trace_callback(logger.debug)

    cache_db_manage(conn)

    delete = []
    for index, item in enumerate(change_data):
        try:
            summary = await get_summary(item, rss.img_proxy)
        except RetryError:
            logger.warning(f"[{item['link']}]的预览图获取失败")
            continue
        is_duplicate, image_hash = await duplicate_exists(
            rss=rss,
            conn=conn,
            item=item,
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
@retry(stop=(stop_after_attempt(5) | stop_after_delay(30)))  # type: ignore
async def get_summary(item: Dict[str, Any], img_proxy: bool) -> str:
    summary = (
        item["content"][0].get("value") if item.get("content") else item["summary"]
    )
    # 如果图片非视频封面，替换为更清晰的预览图；否则移除，以此跳过图片去重检查
    summary_doc = Pq(summary)
    async with aiohttp.ClientSession() as session:
        resp = await session.get(item["link"], proxy=get_proxy(img_proxy))
        d = Pq(await resp.text())
        if img := d("img#image"):
            summary_doc("img").attr("src", img.attr("src"))
        else:
            summary_doc.remove("img")
    return str(summary_doc)
