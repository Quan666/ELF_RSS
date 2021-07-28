import codecs
import json
import os

from pathlib import Path

from ....RSS import rss_class
from ....config import config

FILE_PATH = str(str(Path.cwd()) + os.sep + "data" + os.sep)


# 读取记录
def read_rss(name) -> dict:
    # 检查是否存在rss记录
    json_path = FILE_PATH + (name + ".json")
    if not os.path.isfile(json_path) or os.stat(json_path).st_size == 0:
        return {}
    with codecs.open(json_path, "r", "utf-8") as load_f:
        load_dict = json.load(load_f)
    return load_dict


# 写入记录
def write_rss(name: str, new_rss: dict, new_item: list = None):
    if new_item:
        max_length = len(new_rss.get("entries"))
        # 防止 rss 超过设置的缓存条数
        if max_length >= config.limit:
            limit = max_length + config.limit
        else:
            limit = config.limit
        old = read_rss(name)
        for tmp in new_item:
            old["entries"].insert(0, tmp)
        old["entries"] = old["entries"][0:limit]
    else:
        old = new_rss
    if not os.path.isdir(FILE_PATH):
        os.makedirs(FILE_PATH)
    with codecs.open(FILE_PATH + (name + ".json"), "w", "utf-8") as dump_f:
        dump_f.write(json.dumps(old, sort_keys=True, indent=4, ensure_ascii=False))


# 写入单条消息
def write_item(rss: rss_class.Rss, new_rss: dict, new_item: dict):
    tmp = [new_item]
    write_rss(name=rss.name, new_rss=new_rss, new_item=tmp)
