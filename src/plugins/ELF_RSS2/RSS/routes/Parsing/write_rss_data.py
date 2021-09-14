from tinydb import TinyDB, Query

from .cache_manage import cache_filter


# 写入缓存 json
def write_item(db: TinyDB, new_item: dict):
    db.upsert(cache_filter(new_item), Query().hash == str(new_item.get("hash")))
