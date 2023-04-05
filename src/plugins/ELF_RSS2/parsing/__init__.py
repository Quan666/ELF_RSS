import re
import sqlite3
from difflib import SequenceMatcher
from importlib import import_module
from typing import Any, Dict, List

import arrow
import emoji
from nonebot.log import logger
from pyquery import PyQuery as Pq

from ..config import DATA_PATH, config
from ..rss_class import Rss
from .cache_manage import (
    cache_db_manage,
    cache_json_manage,
    duplicate_exists,
    write_item,
)
from .check_update import check_update, get_item_date
from .download_torrent import down_torrent, pikpak_offline
from .handle_html_tag import handle_html_tag
from .handle_images import handle_img
from .handle_translation import handle_translation
from .parsing_rss import ParsingBase
from .routes import ALL_MODULES
from .send_message import handle_send_msgs
from .utils import get_proxy, get_summary

for module in ALL_MODULES:
    import_module(f".routes.{module}", package=__name__)


# 检查更新
@ParsingBase.append_before_handler()
async def handle_check_update(state: Dict[str, Any]):
    db = state.get("tinydb")
    change_data = check_update(db, state.get("new_data"))
    return {"change_data": change_data}


# 判断是否满足推送条件
@ParsingBase.append_before_handler(priority=11)  # type: ignore
async def handle_check_update(rss: Rss, state: Dict[str, Any]):
    change_data = state.get("change_data")
    db = state.get("tinydb")
    for item in change_data.copy():
        summary = get_summary(item)
        # 检查是否包含屏蔽词
        if config.black_word and re.findall("|".join(config.black_word), summary):
            logger.info("内含屏蔽词，已经取消推送该消息")
            write_item(db, item)
            change_data.remove(item)
            continue
        # 检查是否匹配关键词 使用 down_torrent_keyword 字段,命名是历史遗留导致，实际应该是白名单关键字
        if rss.down_torrent_keyword and not re.search(
            rss.down_torrent_keyword, summary
        ):
            write_item(db, item)
            change_data.remove(item)
            continue
        # 检查是否匹配黑名单关键词 使用 black_keyword 字段
        if rss.black_keyword and (
            re.search(rss.black_keyword, item["title"])
            or re.search(rss.black_keyword, summary)
        ):
            write_item(db, item)
            change_data.remove(item)
            continue
        # 检查是否只推送有图片的消息
        if (rss.only_pic or rss.only_has_pic) and not re.search(
            r"<img[^>]+>|\[img]", summary
        ):
            logger.info(f"{rss.name} 已开启仅图片/仅含有图片，该消息没有图片，将跳过")
            write_item(db, item)
            change_data.remove(item)

    return {"change_data": change_data}


# 如果启用了去重模式，对推送列表进行过滤
@ParsingBase.append_before_handler(priority=12)  # type: ignore
async def handle_check_update(rss: Rss, state: Dict[str, Any]):
    change_data = state.get("change_data")
    conn = state.get("conn")
    db = state.get("tinydb")

    # 检查是否启用去重 使用 duplicate_filter_mode 字段
    if not rss.duplicate_filter_mode:
        return {"change_data": change_data}

    if not conn:
        conn = sqlite3.connect(str(DATA_PATH / "cache.db"))
        conn.set_trace_callback(logger.debug)

    cache_db_manage(conn)

    delete = []
    for index, item in enumerate(change_data):
        is_duplicate, image_hash = await duplicate_exists(
            rss=rss,
            conn=conn,
            item=item,
            summary=get_summary(item),
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


# 处理标题
@ParsingBase.append_handler(parsing_type="title")
async def handle_title(rss: Rss, item: Dict[str, Any]) -> str:
    # 判断是否开启了只推送图片
    if rss.only_pic:
        return ""

    title = item["title"]

    if not config.blockquote:
        title = re.sub(r" - 转发 .*", "", title)

    res = f"标题：{title}\n"
    # 隔开标题和正文
    if not rss.only_title:
        res += "\n"
    if rss.translation:
        res += await handle_translation(content=title)

    # 如果开启了只推送标题，跳过下面判断标题与正文相似度的处理
    if rss.only_title:
        return emoji.emojize(res, language="alias")

    # 判断标题与正文相似度，避免标题正文一样，或者是标题为正文前N字等情况
    try:
        summary_html = Pq(get_summary(item))
        if not config.blockquote:
            summary_html.remove("blockquote")
        similarity = SequenceMatcher(None, summary_html.text()[: len(title)], title)
        # 标题正文相似度
        if similarity.ratio() > 0.6:
            res = ""
    except Exception as e:
        logger.warning(f"{rss.name} 没有正文内容！{e}")

    return emoji.emojize(res, language="alias")


# 处理正文 判断是否是仅推送标题 、是否仅推送图片
@ParsingBase.append_handler(parsing_type="summary", priority=1)
async def handle_summary(rss: Rss, tmp_state: Dict[str, Any]) -> str:
    if rss.only_title or rss.only_pic:
        tmp_state["continue"] = False
    return ""


# 处理正文 处理网页 tag
@ParsingBase.append_handler(parsing_type="summary")  # type: ignore
async def handle_summary(rss: Rss, item: Dict[str, Any], tmp: str) -> str:
    try:
        tmp += handle_html_tag(html=Pq(get_summary(item)))
    except Exception as e:
        logger.warning(f"{rss.name} 没有正文内容！{e}")
    return tmp


# 处理正文 移除指定内容
@ParsingBase.append_handler(parsing_type="summary", priority=11)  # type: ignore
async def handle_summary(rss: Rss, tmp: str) -> str:
    # 移除指定内容
    if rss.content_to_remove:
        for pattern in rss.content_to_remove:
            tmp = re.sub(pattern, "", tmp)
        # 去除多余换行
        while "\n\n\n" in tmp:
            tmp = tmp.replace("\n\n\n", "\n\n")
        tmp = tmp.strip()
    return emoji.emojize(tmp, language="alias")


# 处理正文 翻译
@ParsingBase.append_handler(parsing_type="summary", priority=12)  # type: ignore
async def handle_summary(rss: Rss, tmp: str) -> str:
    if rss.translation:
        tmp += await handle_translation(tmp)
    return tmp


# 处理图片
@ParsingBase.append_handler(parsing_type="picture")
async def handle_picture(rss: Rss, item: Dict[str, Any], tmp: str) -> str:
    # 判断是否开启了只推送标题
    if rss.only_title:
        return ""

    res = ""
    try:
        res += await handle_img(
            item=item,
            img_proxy=rss.img_proxy,
            img_num=rss.max_image_number,
        )
    except Exception as e:
        logger.warning(f"{rss.name} 没有正文内容！{e}")

    # 判断是否开启了只推送图片
    return f"{res}\n" if rss.only_pic else f"{tmp + res}\n"


# 处理来源
@ParsingBase.append_handler(parsing_type="source")
async def handle_source(item: Dict[str, Any]) -> str:
    return f"链接：{item['link']}\n"


# 处理种子
@ParsingBase.append_handler(parsing_type="torrent")
async def handle_torrent(rss: Rss, item: Dict[str, Any]) -> str:
    res: List[str] = []
    if not rss.is_open_upload_group:
        rss.group_id = []
    if rss.down_torrent:
        # 处理种子
        try:
            hash_list = await down_torrent(
                rss=rss, item=item, proxy=get_proxy(rss.img_proxy)
            )
            if hash_list and hash_list[0] is not None:
                res.append("\n磁力：")
                res.extend([f"magnet:?xt=urn:btih:{h}" for h in hash_list])
        except Exception:
            logger.exception("下载种子时出错")
    if rss.pikpak_offline:
        try:
            result = await pikpak_offline(
                rss=rss, item=item, proxy=get_proxy(rss.img_proxy)
            )
            if result:
                res.append("\nPikPak 离线成功")
                res.extend(
                    [
                        f"{r.get('name')}\n{r.get('file_size')} - {r.get('path')}"
                        for r in result
                    ]
                )
        except Exception:
            logger.exception("PikPak 离线时出错")
    return "\n".join(res)


# 处理日期
@ParsingBase.append_handler(parsing_type="date")
async def handle_date(item: Dict[str, Any]) -> str:
    date = get_item_date(item)
    date = date.replace(tzinfo="local") if date > arrow.now() else date.to("local")
    return f"日期：{date.format('YYYY年MM月DD日 HH:mm:ss')}"


# 发送消息
@ParsingBase.append_handler(parsing_type="after")
async def handle_message(
    rss: Rss,
    state: Dict[str, Any],
    item: Dict[str, Any],
    item_msg: str,
) -> str:
    if rss.send_forward_msg:
        return ""

    # 发送消息并写入文件
    await handle_send_msgs(rss=rss, messages=[item_msg], items=[item], state=state)
    return ""


@ParsingBase.append_after_handler()
async def after_handler(rss: Rss, state: Dict[str, Any]) -> Dict[str, Any]:
    if rss.send_forward_msg:
        # 发送消息并写入文件
        await handle_send_msgs(
            rss=rss, messages=state["messages"], items=state["items"], state=state
        )

    db = state["tinydb"]
    new_data_length = len(state["new_data"])
    cache_json_manage(db, new_data_length)

    message_count = len(state["change_data"])
    success_count = message_count - state["error_count"]

    if message_count > 10 and len(state["messages"]) == 10:
        return {}

    if success_count > 0:
        logger.info(f"{rss.name} 新消息推送完毕，共计：{success_count}/{message_count}")
    elif message_count > 0:
        logger.error(f"{rss.name} 新消息推送失败，共计：{message_count}")
    else:
        logger.info(f"{rss.name} 没有新信息")

    if conn := state["conn"]:
        conn.close()

    db.close()

    return {}
