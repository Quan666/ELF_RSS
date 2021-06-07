# 将 dict 对象转换为 json 字符串后，计算哈希值，供后续比较
import hashlib
import json
import time
from typing import Dict, Any


def dict_hash(dictionary: Dict[str, Any]) -> str:
    dictionary_temp = dictionary.copy()
    # 避免部分缺失 published_parsed 的消息导致检查更新出问题，进行过滤
    if dictionary.get("published_parsed"):
        dictionary_temp.pop("published_parsed")
    # 某些情况下，如微博带视频的消息，正文可能不一样，先过滤
    dictionary_temp.pop("summary")
    if dictionary.get("summary_detail"):
        dictionary_temp.pop("summary_detail")
    d_hash = hashlib.md5()
    encoded = json.dumps(dictionary_temp, sort_keys=True).encode()
    d_hash.update(encoded)
    return d_hash.hexdigest()

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

# 检查更新
async def check_update(new: list, old: list) -> list:
    old_hash_list = [dict_hash(i) if not i.get("hash") else i.get("hash") for i in old]
    # 对比本地消息缓存和获取到的消息，新的存入 hash ，随着检查更新的次数增多，逐步替换原来没存 hash 的缓存记录
    temp = []
    for i in new:
        hash_temp = dict_hash(i)
        if hash_temp not in old_hash_list:
            i["hash"] = hash_temp
            temp.append(i)
    # 将结果进行去重，避免消息重复发送
    temp = [value for index, value in enumerate(temp) if value not in temp[index + 1:]]
    # 因为最新的消息会在最上面，所以要反转处理（主要是为了那些缺失 published_parsed 的消息）
    result = []
    for t in temp:
        result.insert(0, t)
    # 对结果按照发布时间排序
    result_with_date = [
        (await handle_date(i.get("published_parsed")), i) for i in result
    ]
    result_with_date.sort(key=lambda tup: tup[0])
    result = [i for key, i in result_with_date]
    return result
