import re
from typing import Any, Dict, Optional

from ..config import config


# 代理
def get_proxy(open_proxy: bool) -> Optional[str]:
    if not open_proxy or not config.rss_proxy:
        return None
    return f"http://{config.rss_proxy}"


# 获取正文
def get_summary(item: Dict[str, Any]) -> str:
    summary: str = (
        item["content"][0]["value"] if item.get("content") else item["summary"]
    )
    return f"<div>{summary}</div>" if re.search("^https?://", summary) else summary


def get_author(item: Dict[str, Any]) -> str:
    return item.get("author", "")
