import re
from typing import Any, Dict, List

from tinydb import Query, TinyDB

from ..rss_class import Rss
from .Parsing import ParsingBase
from .Parsing.check_update import get_item_date


# 检查更新
@ParsingBase.append_before_handler(rex="nga", priority=10)
async def handle_check_update(rss: Rss, state: Dict[str, Any]) -> Dict[str, Any]:
    new_data = state["new_data"]
    db = state["tinydb"]

    for i in new_data:
        i["link"] = re.sub(r"&rand=\d+", "", i["link"])

    change_data = await check_update(db, new_data)
    return {"change_data": change_data}


# 检查更新
async def check_update(db: TinyDB, new: List[Dict[str, Any]]) -> List[Dict[str, Any]]:

    # 发送失败超过 3 次的消息不再发送
    to_send_list: List[Dict[str, Any]] = db.search(
        (Query().to_send.exists()) & (Query().count <= 3)
    )

    if not new and not to_send_list:
        return []

    old_link_list = [i["id"] for i in db.all()]
    to_send_list.extend([i for i in new if i["link"] not in old_link_list])

    # 对结果按照发布时间排序
    to_send_list.sort(key=get_item_date)

    return to_send_list
