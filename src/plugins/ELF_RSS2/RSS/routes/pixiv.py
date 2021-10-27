import re

from tinydb import TinyDB, Query

from .Parsing import ParsingBase
from .Parsing.check_update import get_item_date
from ..rss_class import Rss


# 处理来源
@ParsingBase.append_handler(parsing_type="source", rex="pixiv")
async def handle_source(
    rss: Rss, state: dict, item: dict, item_msg: str, tmp: str, tmp_state: dict
) -> str:
    source = item["link"]
    # 缩短 pixiv 链接
    str_link = re.sub("https://www.pixiv.net/artworks/", "https://pixiv.net/i/", source)
    return "链接：" + str_link + "\n"


# 检查更新
@ParsingBase.append_before_handler(rex="pixiv/ranking", priority=10)
async def handle_check_update(rss: Rss, state: dict):
    db = state.get("tinydb")
    change_data = await check_update(db, state.get("new_data"))
    return {"change_data": change_data}


# 检查更新
async def check_update(db: TinyDB, new: list) -> list:

    # 发送失败超过 3 次的消息不再发送
    to_send_list = db.search((Query().to_send.exists()) & (Query().count <= 3))

    if not new and not to_send_list:
        return []

    old_link_list = [i["link"] for i in db.all()]
    to_send_list.extend([i for i in new if i["link"] not in old_link_list])

    # 对结果按照发布时间排序
    to_send_list.sort(key=get_item_date)

    return to_send_list
