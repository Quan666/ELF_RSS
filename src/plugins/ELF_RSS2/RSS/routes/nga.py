import re

from .Parsing import ParsingBase, check_update

from ..rss_class import Rss


# 检查更新
@ParsingBase.append_before_handler(rex="nga", priority=10)
async def handle_check_update(rss: Rss, state: dict):
    new_data = state.get("new_data")
    old_data = state.get("old_data")

    for i in new_data:
        i["link"] = re.sub(r"&rand=\d+", "", i["link"])

    for i in old_data:
        i["link"] = re.sub(r"&rand=\d+", "", i["link"])

    change_data = await check_update.check_update(new_data, old_data)
    return {"change_data": change_data}
