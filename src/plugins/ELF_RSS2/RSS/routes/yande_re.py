import re
from typing import Any, Dict

from ..rss_class import Rss
from .Parsing import ParsingBase, check_update


# 检查更新
@ParsingBase.append_before_handler(
    priority=10, rex=r"https\:\/\/yande\.re\/post\/piclens\?tags\="
)
async def handle_check_update(rss: Rss, state: Dict[str, Any]) -> Dict[str, Any]:
    db = state["tinydb"]
    change_data = await check_update(db, state["new_data"])
    for i in change_data:
        if i.get("media_content"):
            i["summary"] = re.sub(
                r'https://[^"]+', i["media_content"][0]["url"], i["summary"]
            )
    return {"change_data": change_data}
