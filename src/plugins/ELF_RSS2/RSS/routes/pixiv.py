import re
import os

from pathlib import Path
from .Parsing import ParsingBase
from ..rss_class import Rss

FILE_PATH = str(str(Path.cwd()) + os.sep + "data" + os.sep)

import hashlib
import time

from tinydb import TinyDB, Query
from typing import Dict, Any


# 处理日期
async def handle_date(date=None) -> str:
    if date:
        if not isinstance(date, tuple):
            date = tuple(date)
        rss_time = time.mktime(date)
        # 时差处理，待改进
        if rss_time + 28800.0 < time.time():
            rss_time += 28800.0
        return "日期：" + time.strftime("%m月%d日 %H:%M:%S", time.localtime(rss_time))
    # 没有日期的情况，以当前时间
    else:
        return "日期：" + time.strftime("%m月%d日 %H:%M:%S", time.localtime())


# 对 dict 对象计算哈希值，供后续比较
def dict_hash(dictionary: Dict[str, Any]) -> str:
    keys = ["id", "link"]
    string = "|".join([dictionary[k] for k in keys if k in dictionary])
    result = hashlib.md5(string.encode())
    return result.hexdigest()


# 检查更新
async def check_update(_file: str, new: list) -> list:
    db = TinyDB(
        _file,
        encoding="utf-8",
        sort_keys=True,
        indent=4,
        ensure_ascii=False,
    )
    # 发送失败超过 3 次的消息不再发送
    to_send_list = db.search(
        (Query().to_send.exists()) & (Query().count.test(lambda x: x <= 3))
    )

    if not new and not to_send_list:
        return []

    old_hash_list = [r.get("hash") for r in db.all()]
    for i in new:
        hash_temp = dict_hash(i)
        if hash_temp not in old_hash_list:
            i["hash"] = hash_temp
            to_send_list.append(i)

    # 对结果按照发布时间排序
    result_with_date = [
        (await handle_date(i.get("updated_parsed")), i)
        if i.get("updated_parsed")
        else (await handle_date(i.get("published_parsed")), i)
        for i in to_send_list
    ]
    result_with_date.sort(key=lambda tup: tup[0])
    result = [i for key, i in result_with_date]

    return result


# 处理来源
@ParsingBase.append_handler(parsing_type="source", rex="pixiv", priority=10, block=True)
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
