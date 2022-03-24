import re
from typing import Any, Dict, Union

import httpx
from httpx import Proxy

from ....config import config


# 代理
def get_proxy(open_proxy: bool) -> Union[Proxy, Dict[Any, Any]]:
    if not open_proxy or not config.rss_proxy:
        return {}
    return Proxy(url=f"http://{config.rss_proxy}")


# 获取正文
def get_summary(item: Dict[str, Any]) -> str:
    summary: str = (
        item["content"][0]["value"] if item.get("content") else item["summary"]
    )
    if re.search("^https?://", summary):
        return f"<div>{summary}</div>"
    return summary
