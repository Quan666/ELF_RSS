import os

from pathlib import Path
from tinydb import TinyDB, Query

FILE_PATH = str(str(Path.cwd()) + os.sep + "data" + os.sep)


# 读取记录
def read_rss(name: str) -> list:
    _file = FILE_PATH + (name + ".json")
    db = TinyDB(
        _file,
        encoding="utf-8",
        sort_keys=True,
        indent=4,
        ensure_ascii=False,
    )
    return db.all()


# 写入单条消息
def write_item(name: str, new_item: dict):
    _file = FILE_PATH + (name + ".json")
    db = TinyDB(
        _file,
        encoding="utf-8",
        sort_keys=True,
        indent=4,
        ensure_ascii=False,
    )
    db.upsert(new_item, Query().hash == str(new_item.get("hash")))
