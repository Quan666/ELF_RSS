import difflib
import re
import sqlite3
from email.utils import parsedate_to_datetime
from typing import Any, Dict

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
    insert_into_cache_db,
    write_item,
)
from .check_update import check_update
from .download_torrent import down_torrent
from .handle_html_tag import handle_bbcode, handle_html_tag
from .handle_images import handle_img
from .handle_translation import handle_translation
from .parsing_rss import ParsingBase
from .routes import *
from .send_message import send_msg
from .utils import get_proxy, get_summary


# 检查更新
@ParsingBase.append_before_handler(priority=10)
async def handle_check_update(rss: Rss, state: Dict[str, Any]):
    db = state.get("tinydb")
    change_data = check_update(db, state.get("new_data"))
    return {"change_data": change_data}


# 判断是否满足推送条件
@ParsingBase.append_before_handler(priority=11)
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
@ParsingBase.append_before_handler(priority=12)
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
async def handle_title(
    rss: Rss,
    state: Dict[str, Any],
    item: Dict[str, Any],
    item_msg: str,
    tmp: str,
    tmp_state: Dict[str, Any],
) -> str:
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
        return emoji.emojize(res, use_aliases=True)

    # 判断标题与正文相似度，避免标题正文一样，或者是标题为正文前N字等情况
    try:
        summary_html = Pq(get_summary(item))
        if not config.blockquote:
            summary_html.remove("blockquote")
        similarity = difflib.SequenceMatcher(
            None, summary_html.text()[: len(title)], title
        )
        # 标题正文相似度
        if similarity.ratio() > 0.6:
            res = ""
    except Exception as e:
        logger.warning(f"{rss.name} 没有正文内容！{e}")

    return emoji.emojize(res, use_aliases=True)


# 处理正文 判断是否是仅推送标题 、是否仅推送图片
@ParsingBase.append_handler(parsing_type="summary", priority=1)
async def handle_summary(
    rss: Rss,
    state: Dict[str, Any],
    item: Dict[str, Any],
    item_msg: str,
    tmp: str,
    tmp_state: Dict[str, Any],
) -> str:
    if rss.only_title or rss.only_pic:
        tmp_state["continue"] = False
    return ""


# 处理正文 处理网页 tag
@ParsingBase.append_handler(parsing_type="summary", priority=10)
async def handle_summary(
    rss: Rss,
    state: Dict[str, Any],
    item: Dict[str, Any],
    item_msg: str,
    tmp: str,
    tmp_state: Dict[str, Any],
) -> str:
    try:
        tmp += handle_html_tag(html=Pq(get_summary(item)))
    except Exception as e:
        logger.warning(f"{rss.name} 没有正文内容！{e}")
    return tmp


# 处理正文 移除指定内容
@ParsingBase.append_handler(parsing_type="summary", priority=11)
async def handle_summary(
    rss: Rss,
    state: Dict[str, Any],
    item: Dict[str, Any],
    item_msg: str,
    tmp: str,
    tmp_state: Dict[str, Any],
) -> str:
    # 移除指定内容
    if rss.content_to_remove:
        for pattern in rss.content_to_remove:
            tmp = re.sub(pattern, "", tmp)
        # 去除多余换行
        while "\n\n\n" in tmp:
            tmp = tmp.replace("\n\n\n", "\n\n")
        tmp = tmp.strip()
    return emoji.emojize(tmp, use_aliases=True)


# 处理正文 翻译
@ParsingBase.append_handler(parsing_type="summary", priority=12)
async def handle_summary(
    rss: Rss,
    state: Dict[str, Any],
    item: Dict[str, Any],
    item_msg: str,
    tmp: str,
    tmp_state: Dict[str, Any],
) -> str:
    if rss.translation:
        tmp += await handle_translation(tmp)
    return tmp


# 处理图片
@ParsingBase.append_handler(parsing_type="picture")
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
    if rss.only_pic:
        return f"{res}\n"

    return f"{tmp + res}\n"


# 处理来源
@ParsingBase.append_handler(parsing_type="source")
async def handle_source(
    rss: Rss,
    state: Dict[str, Any],
    item: Dict[str, Any],
    item_msg: str,
    tmp: str,
    tmp_state: Dict[str, Any],
) -> str:
    return f"链接：{item['link']}\n"


# 处理种子
@ParsingBase.append_handler(parsing_type="torrent")
async def handle_torrent(
    rss: Rss,
    state: Dict[str, Any],
    item: Dict[str, Any],
    item_msg: str,
    tmp: str,
    tmp_state: Dict[str, Any],
) -> str:
    res = ""
    if not rss.is_open_upload_group:
        rss.group_id = []
    if rss.down_torrent:
        # 处理种子
        try:
            hash_list = await down_torrent(
                rss=rss, item=item, proxy=get_proxy(rss.img_proxy)
            )
            if hash_list and hash_list[0] is not None:
                res = "\n磁力：\n" + "\n".join(
                    [f"magnet:?xt=urn:btih:{h}" for h in hash_list]
                )
        except Exception:
            logger.exception("下载种子时出错")
    return res


# 处理日期
@ParsingBase.append_handler(parsing_type="date")
async def handle_date(
    rss: Rss,
    state: Dict[str, Any],
    item: Dict[str, Any],
    item_msg: str,
    tmp: str,
    tmp_state: Dict[str, Any],
) -> str:
    date = item.get("published", item.get("updated"))
    if date:
        try:
            date = parsedate_to_datetime(date)
        except TypeError:
            pass
        finally:
            date = arrow.get(date).to("Asia/Shanghai")
    else:
        date = arrow.now()
    return f"日期：{date.format('YYYY年MM月DD日 HH:mm:ss')}"


# 发送消息
@ParsingBase.append_handler(parsing_type="after")
async def handle_message(
    rss: Rss,
    state: Dict[str, Any],
    item: Dict[str, Any],
    item_msg: str,
    tmp: str,
    tmp_state: Dict[str, Any],
) -> str:
    db = state["tinydb"]

    # 发送消息并写入文件
    if await send_msg(rss=rss, msg=item_msg, item=item):

        if rss.duplicate_filter_mode:
            insert_into_cache_db(
                conn=state["conn"], item=item, image_hash=item["image_hash"]
            )

        if item.get("to_send"):
            item.pop("to_send")

        state["item_count"] += 1
    else:
        item["to_send"] = True

    write_item(db, item)

    return ""


@ParsingBase.append_after_handler()
async def after_handler(rss: Rss, state: Dict[str, Any]) -> Dict[str, Any]:
    item_count: int = state["item_count"]
    conn = state["conn"]
    db = state["tinydb"]

    if item_count > 0:
        logger.info(f"{rss.name} 新消息推送完毕，共计：{item_count}")
    else:
        logger.info(f"{rss.name} 没有新信息")

    if conn is not None:
        conn.close()

    new_data_length = len(state["new_data"])
    cache_json_manage(db, new_data_length)
    db.close()

    return {}
