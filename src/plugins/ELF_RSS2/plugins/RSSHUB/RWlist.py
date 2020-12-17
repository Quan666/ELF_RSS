import codecs
import json
import os
import os.path
from pathlib import Path

from . import RSS_class

# 存储目录
file_path = Path.cwd() / 'data'


# 读取记录
def readRss() -> list:
    rss_list = []
    with codecs.open(str(file_path / "rss.json"), 'r', 'utf-8') as load_f:
        rss_list_json = json.load(load_f)
        for rss_one in rss_list_json:
            tmp_rss = RSS_class.rss('', '', '', '')
            tmp_rss.__dict__ = json.loads(rss_one)
            rss_list.append(tmp_rss)
    return rss_list


# 写入记录
def writeRss(rss_list: list):
    rss_json = []
    for rss_one in rss_list:
        rss_json.append(json.dumps(rss_one.__dict__, sort_keys=True, indent=4, ensure_ascii=False))
    if not os.path.isdir(file_path):
        os.makedirs(file_path)
    with codecs.open(str(file_path / "rss.json"), "w", 'utf-8') as dump_f:
        dump_f.write(json.dumps(rss_json, sort_keys=True, indent=4, ensure_ascii=False))
