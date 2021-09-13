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
    result_with_date = [
        (await handle_date(i.get("updated_parsed")), i)
        if i.get("updated_parsed")
        else (await handle_date(i.get("published_parsed")), i)
        for i in to_send_list
    ]
    result_with_date.sort(key=lambda tup: tup[0])
    result = [i for key, i in result_with_date]

    return result
