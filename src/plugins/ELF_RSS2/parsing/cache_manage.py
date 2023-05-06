from io import BytesIO
from sqlite3 import Connection
from typing import Any, Dict, Optional, Tuple

import imagehash
from nonebot.log import logger
from PIL import Image, UnidentifiedImageError
from pyquery import PyQuery as Pq
from tinydb import Query, TinyDB
from tinydb.operations import delete

from ..config import config
from ..rss_class import Rss
from .check_update import get_item_date
from .handle_images import download_image


# 精简 xxx.json (缓存) 中的字段
def cache_filter(data: Dict[str, Any]) -> Dict[str, Any]:
    keys = [
        "guid",
        "link",
        "published",
        "updated",
        "title",
        "hash",
    ]
    if data.get("to_send"):
        keys += [
            "content",
            "summary",
            "to_send",
        ]
    return {k: v for k in keys if (v := data.get(k))}


# 对去重数据库进行管理
def cache_db_manage(conn: Connection) -> None:
    cursor = conn.cursor()
    # 用来去重的 sqlite3 数据表如果不存在就创建一个
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS main (
        "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        "link" TEXT,
        "title" TEXT,
        "image_hash" TEXT,
        "datetime" TEXT DEFAULT (DATETIME('Now', 'LocalTime'))
    );
    """
    )
    cursor.close()
    conn.commit()
    cursor = conn.cursor()
    # 移除超过 config.db_cache_expire 天没重复过的记录
    cursor.execute(
        "DELETE FROM main WHERE datetime <= DATETIME('Now', 'LocalTime', ?);",
        (f"-{config.db_cache_expire} Day",),
    )
    cursor.close()
    conn.commit()


# 对缓存 json 进行管理
def cache_json_manage(db: TinyDB, new_data_length: int) -> None:
    # 只保留最多 config.limit + new_data_length 条的记录
    limit = config.limit + new_data_length
    retains = db.all()
    retains.sort(key=get_item_date)
    retains = retains[-limit:]
    db.truncate()
    db.insert_multiple(retains)


async def get_image_hash(rss: Rss, summary: str, item: Dict[str, Any]) -> Optional[str]:
    try:
        summary_doc = Pq(summary)
    except Exception as e:
        logger.warning(e)
        # 没有正文内容直接跳过
        return None

    img_doc = summary_doc("img")
    # 只处理仅有一张图片的情况
    if len(img_doc) != 1:
        return None

    url = img_doc.attr("src")
    # 通过图像的指纹来判断是否实际是同一张图片
    content = await download_image(url, rss.img_proxy)

    if not content:
        return None

    try:
        im = Image.open(BytesIO(content))
    except UnidentifiedImageError:
        return None

    item["image_content"] = content
    # GIF 图片的 image_hash 实际上是第一帧的值，为了避免误伤直接跳过
    if im.format == "GIF":
        item["gif_url"] = url
        return None

    return str(imagehash.dhash(im))


# 去重判断
async def duplicate_exists(
    rss: Rss, conn: Connection, item: Dict[str, Any], summary: str
) -> Tuple[bool, Optional[str]]:
    flag = False
    link = item["link"].replace("'", "''")
    title = item["title"].replace("'", "''")
    image_hash = None
    cursor = conn.cursor()
    sql = "SELECT * FROM main WHERE 1=1"
    args = []

    for mode in rss.duplicate_filter_mode:
        if mode == "image":
            image_hash = await get_image_hash(rss, summary, item)
            if image_hash:
                sql += " AND image_hash=?"
                args.append(image_hash)
        elif mode == "link":
            sql += " AND link=?"
            args.append(link)
        elif mode == "title":
            sql += " AND title=?"
            args.append(title)

    if "or" in rss.duplicate_filter_mode:
        sql = sql.replace("AND", "OR").replace("OR", "AND", 1)

    cursor.execute(f"{sql};", args)
    result = cursor.fetchone()

    if result is not None:
        result_id = result[0]
        cursor.execute(
            "UPDATE main SET datetime = DATETIME('Now','LocalTime') WHERE id = ?;",
            (result_id,),
        )
        cursor.close()
        conn.commit()
        flag = True

    return flag, image_hash


# 消息发送后存入去重数据库
def insert_into_cache_db(
    conn: Connection, item: Dict[str, Any], image_hash: str
) -> None:
    cursor = conn.cursor()
    link = item["link"].replace("'", "''")
    title = item["title"].replace("'", "''")
    cursor.execute(
        "INSERT INTO main (link, title, image_hash) VALUES (?, ?, ?);",
        (link, title, image_hash),
    )
    cursor.close()
    conn.commit()


# 写入缓存 json
def write_item(db: TinyDB, new_item: Dict[str, Any]) -> None:
    if not new_item.get("to_send"):
        db.update(delete("to_send"), Query().hash == str(new_item.get("hash")))  # type: ignore
    db.upsert(cache_filter(new_item), Query().hash == str(new_item.get("hash")))
