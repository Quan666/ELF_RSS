import os

from pathlib import Path
from tinydb import TinyDB, Query

from .cache_manage import cache_filter

FILE_PATH = str(str(Path.cwd()) + os.sep + "data" + os.sep)


# 写入缓存 json
def write_item(db: TinyDB, new_item: dict):
    db.upsert(cache_filter(new_item), Query().hash == str(new_item.get("hash")))
