import arrow
import hashlib

from arrow import Arrow
from email.utils import parsedate_to_datetime

from tinydb import TinyDB, Query
from typing import Dict, Any


# 对 dict 对象计算哈希值，供后续比较
def dict_hash(dictionary: Dict[str, Any]) -> str:
    keys = ["id", "link", "published", "updated", "title"]
    string = "|".join([dictionary[k] for k in keys if k in dictionary])
    result = hashlib.md5(string.encode())
    return result.hexdigest()


# 检查更新
async def check_update(db: TinyDB, new: list) -> list:

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
    to_send_list.sort(key=get_item_date)

    return to_send_list


def get_item_date(item: dict) -> Arrow:
    date = item.get("published", item.get("updated"))
    try:
        date = parsedate_to_datetime(date)
    except TypeError:
        pass
    finally:
        date = arrow.get(date)
    return date
