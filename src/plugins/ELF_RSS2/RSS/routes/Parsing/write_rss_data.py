from tinydb import Query, TinyDB
from tinydb.operations import delete

from .cache_manage import cache_filter


# 写入缓存 json
def write_item(db: TinyDB, new_item: dict):
    if not new_item.get("to_send"):
        db.update_multiple(
            [
                (delete("to_send"), Query().hash == str(new_item.get("hash"))),
                (delete("count"), Query().hash == str(new_item.get("hash"))),
            ]
        )
    db.upsert(cache_filter(new_item), Query().hash == str(new_item.get("hash")))
