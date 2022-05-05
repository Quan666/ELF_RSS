import hashlib
from email.utils import parsedate_to_datetime
from typing import Any, Dict, List

import arrow
from arrow import Arrow
from tinydb import Query, TinyDB


# 对 dict 对象计算哈希值，供后续比较
def dict_hash(dictionary: Dict[str, Any]) -> str:
    string = str(dictionary.get("guid", dictionary.get("link")))
    result = hashlib.md5(string.encode())
    return result.hexdigest()


# 检查更新
def check_update(db: TinyDB, new: List[Dict[str, Any]]) -> List[Dict[str, Any]]:

    # 发送失败 1 次
    to_send_list: List[Dict[str, Any]] = db.search(Query().to_send.exists())

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


def get_item_date(item: Dict[str, Any]) -> Arrow:
    if date := item.get("published", item.get("updated")):
        try:
            date = parsedate_to_datetime(date)
        except TypeError:
            pass
        return arrow.get(date)
    return arrow.now()
