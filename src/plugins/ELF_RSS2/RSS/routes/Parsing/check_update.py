import hashlib
import json
import time

from typing import Dict, Any


# 处理日期
async def handle_date(date=None) -> str:
    if date:
        rss_time = time.mktime(date)
        # 时差处理，待改进
        if rss_time + 28800.0 < time.time():
            rss_time += 28800.0
        return "日期：" + time.strftime("%m月%d日 %H:%M:%S", time.localtime(rss_time))
    # 没有日期的情况，以当前时间
    else:
        return "日期：" + time.strftime("%m月%d日 %H:%M:%S", time.localtime())


# 将 dict 对象转换为 json 字符串后，计算哈希值，供后续比较
def dict_hash(dictionary: Dict[str, Any]) -> str:
    keys = ["id", "link", "published", "updated", "title"]
    dictionary_temp = {k: dictionary[k] for k in keys if k in dictionary}
    d_hash = hashlib.md5()
    encoded = json.dumps(dictionary_temp, sort_keys=True).encode()
    d_hash.update(encoded)
    return d_hash.hexdigest()


# 检查更新
async def check_update(new: list, old: list) -> list:
    # 有些订阅可能存在没有 entries 的情况，比如 Bilibili 直播间开播状态，直接跳过
    if not new:
        return []

    old_hash_list = [dict_hash(i) if not i.get("hash") else i.get("hash") for i in old]
    # 对比本地消息缓存和获取到的消息，新的存入 hash ，随着检查更新的次数增多，逐步替换原来没存 hash 的缓存记录
    temp = []
    hash_list = []
    for i in new:
        hash_temp = dict_hash(i)
        if hash_temp not in old_hash_list:
            i["hash"] = hash_temp
            temp.append(i)
            hash_list.append(hash_temp)

    # 将结果进行去重，避免消息重复发送
    result = [
        value
        for index, value in enumerate(temp)
        if value["hash"] not in hash_list[index + 1 :]
    ]

    # 对结果按照发布时间排序
    result_with_date = [
        (await handle_date(i.get("updated_parsed")), i)
        if i.get("updated_parsed")
        else (await handle_date(i.get("published_parsed")), i)
        for i in result
    ]
    result_with_date.sort(key=lambda tup: tup[0])
    result = [i for key, i in result_with_date]

    return result
