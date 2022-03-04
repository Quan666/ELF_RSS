# -*- coding: UTF-8 -*-

import asyncio
import re
from pathlib import Path

import feedparser
import httpx
from nonebot.log import logger
from tenacity import (
    RetryError,
    TryAgain,
    retry,
    stop_after_attempt,
    stop_after_delay,
    wait_fixed,
)
from tinydb import TinyDB
from tinydb.middlewares import CachingMiddleware
from tinydb.storages import JSONStorage

from ..config import DATA_PATH, config
from . import rss_class
from .routes.Parsing import ParsingRss, get_proxy
from .routes.Parsing.cache_manage import cache_filter
from .routes.Parsing.check_update import dict_hash

STATUS_CODE = [200, 301, 302]
# 去掉烦人的 returning true from eof_received() has no effect when using ssl httpx 警告
asyncio.log.logger.setLevel(40)
HEADERS = {
    "Accept": "application/xhtml+xml,application/xml,*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Cache-Control": "max-age=0",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36",
    "Connection": "keep-alive",
    "Content-Type": "application/xml; charset=utf-8",
}


# 入口
async def start(rss: rss_class.Rss) -> None:
    # 网络加载 新RSS
    # 读取 旧RSS 记录
    # 检查更新
    # 对更新的 RSS 记录列表进行处理，当发送成功后才写入，成功一条写一条

    try:
        new_rss = await get_rss(rss)
    except RetryError:
        cookies_str = "及 cookies " if rss.cookies else ""
        logger.error(f"{rss.name}[{rss.get_url()}]抓取失败！已达最大重试次数！请检查订阅地址{cookies_str}！")
        return
    # 检查是否存在rss记录
    _file = DATA_PATH / (rss.name + ".json")
    if not Path.exists(_file):
        db = TinyDB(
            _file,
            storage=CachingMiddleware(JSONStorage),
            encoding="utf-8",
            sort_keys=True,
            indent=4,
            ensure_ascii=False,
        )
        entries = new_rss.get("entries")
        result = []
        for i in entries:
            i["hash"] = dict_hash(i)
            result.append(cache_filter(i))
        db.insert_multiple(result)
        db.close()
        logger.info(f"{rss.name} 第一次抓取成功！")
        return

    pr = ParsingRss(rss=rss)
    await pr.start(rss_name=rss.name, new_rss=new_rss)


# 获取 RSS 并解析为 json ，失败重试
@retry(wait=wait_fixed(1), stop=(stop_after_attempt(5) | stop_after_delay(30)))
async def get_rss(rss: rss_class.Rss) -> dict:
    proxies = get_proxy(rss.img_proxy)
    # 对本机部署的 RSSHub 不使用代理
    no_proxy = [
        "localhost",
        "127.0.0.1",
    ]
    for i in no_proxy:
        if i in rss.get_url():
            proxies = None

    # 判断是否使用cookies
    cookies = rss.cookies if rss.cookies else None

    # 获取 xml
    d = None
    async with httpx.AsyncClient(
        proxies=proxies, cookies=cookies, headers=HEADERS
    ) as client:
        try:
            r = await client.get(rss.get_url())
            # 解析为 JSON
            if r.status_code in STATUS_CODE:
                d = feedparser.parse(r.content)
            else:
                raise httpx.HTTPStatusError
        except Exception:
            if (
                not re.match("[hH][tT]{2}[pP][sS]?://", rss.url, flags=0)
                and config.rsshub_backup
            ):
                logger.warning(f"[{rss.get_url()}]访问失败！将使用备用 RSSHub 地址！")
                for rsshub_url in list(config.rsshub_backup):
                    try:
                        r = await client.get(rss.get_url(rsshub=rsshub_url))
                        if r.status_code in STATUS_CODE:
                            d = feedparser.parse(r.content)
                        else:
                            raise httpx.HTTPStatusError
                    except Exception:
                        logger.warning(
                            f"[{rss.get_url(rsshub=rsshub_url)}]访问失败！将使用备用 RSSHub 地址！"
                        )
                        continue
                    if d.get("feed"):
                        logger.info(f"[{rss.get_url(rsshub=rsshub_url)}]抓取成功！")
                        break
        finally:
            if not d or not d.get("feed"):
                logger.warning(f"{rss.name} 抓取失败！将重试最多 5 次！")
                raise TryAgain
    return d
