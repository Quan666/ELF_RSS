import re
import os

from pathlib import Path
from .Parsing import ParsingBase
from ..rss_class import Rss

FILE_PATH = str(str(Path.cwd()) + os.sep + "data" + os.sep)

import hashlib
import arrow

from tinydb import TinyDB, Query
from typing import Dict, Any
from arrow import Arrow
from email.utils import parsedate_to_datetime

# 对 dict 对象计算哈希值，供后续比较
def dict_hash(dictionary: Dict[str, Any]) -> str:
    keys = ["id", "link"]
    string = "|".join([dictionary[k] for k in keys if k in dictionary])
    result = hashlib.md5(string.encode())
    return result.hexdigest()


# 检查更新
async def check_update(db: TinyDB, new: list) -> list:

    # 发送失败超过 3 次的消息不再发送
    to_send_list = db.search((Query().to_send.exists()) & (Query().count <= 3))

    if not new and not to_send_list:
        return []

    old_hash_list = [r.get("hash") for r in db.all()]
    for i in new:
        hash_temp = dict_hash(i)
        if hash_temp not in old_hash_list:
            i["hash"] = hash_temp
            to_send_list.append(i)

    # 对结果按照发布时间排序
    to_send_list.sort(key=get_item_date)

    return to_send_list


def get_item_date(item: dict) -> Arrow:
    date = item.get("published", item.get("updated"))
    if date:
        try:
            date = parsedate_to_datetime(date)
        except TypeError:
            pass
        finally:
            date = arrow.get(date)
    else:
        date = arrow.now()
    return date


# 处理来源
@ParsingBase.append_handler(parsing_type="source", rex="pixiv")
async def handle_source(
    rss: Rss, state: dict, item: dict, item_msg: str, tmp: str, tmp_state: dict
) -> str:
    source = item["link"]
    # 缩短 pixiv 链接
    str_link = re.sub("https://www.pixiv.net/artworks/", "https://pixiv.net/i/", source)
    return "链接：" + str_link + "\n"


# 检查更新
@ParsingBase.append_before_handler(priority=10, rex="/pixiv/ranking/day")
async def handle_check_update(rss: Rss, state: dict):
    _file = FILE_PATH + (rss.name + ".json")
    change_data = await check_update(_file, state.get("new_data"))
    return {"change_data": change_data}
