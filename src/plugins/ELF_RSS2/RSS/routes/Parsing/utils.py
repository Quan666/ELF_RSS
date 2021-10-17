import httpx

from ....config import config


# 代理
def get_proxy(open_proxy: bool) -> dict:
    if not open_proxy:
        return {}
    proxy = config.rss_proxy
    return (
        httpx.Proxy(
            url="http://" + proxy,
            mode="DEFAULT",
        )
        if proxy
        else {}
    )


# 获取正文
def get_summary(item: dict):
    return item["content"][0].get("value") if item.get("content") else item["summary"]
