import asyncio
from random import randint
from typing import Any, Dict, Tuple

import aiohttp
import feedparser
from nonebot.log import logger
from tinydb import TinyDB
from tinydb.middlewares import CachingMiddleware
from tinydb.storages import JSONStorage
from yarl import URL

from . import my_trigger as tr
from .config import DATA_PATH, config
from .parsing import get_proxy, send_msg
from .parsing.cache_manage import cache_filter
from .parsing.check_update import dict_hash
from .parsing.parsing_rss import ParsingRss
from .rss_class import Rss
from .utils import get_http_caching_headers

HEADERS = {
    "Accept": "application/xhtml+xml,application/xml,*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Cache-Control": "max-age=0",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36",
    "Connection": "keep-alive",
    "Content-Type": "application/xml; charset=utf-8",
}


# 抓取 feed，读取缓存，检查更新，对更新进行处理
async def start(rss: Rss) -> None:
    new_rss, cached = await fetch_rss(rss)
    # 检查是否存在rss记录
    _file = DATA_PATH / f"{Rss.handle_name(rss.name)}.json"
    first_time_fetch = not _file.exists()
    if cached:
        logger.info(f"{rss.name} 没有新信息")
        return
    if not new_rss or not new_rss.get("feed"):
        rss.error_count += 1
        logger.warning(f"{rss.name} 抓取失败！")
        if first_time_fetch:
            # 第一次抓取失败，如果配置了代理，则自动使用代理抓取
            if config.rss_proxy and not rss.img_proxy:
                rss.img_proxy = True
                logger.info(f"{rss.name} 第一次抓取失败，自动使用代理抓取")
                await start(rss)
            else:
                await auto_stop_and_notify_all(rss)
        if rss.error_count >= 100:
            await auto_stop_and_notify_all(rss)
        return
    if new_rss.get("feed") and rss.error_count > 0:
        rss.error_count = 0
    if first_time_fetch:
        with TinyDB(
            _file,
            storage=CachingMiddleware(JSONStorage),  # type: ignore
            encoding="utf-8",
            sort_keys=True,
            indent=4,
            ensure_ascii=False,
        ) as db:
            entries = new_rss["entries"]
            result = []
            for i in entries:
                i["hash"] = dict_hash(i)
                result.append(cache_filter(i))
            db.insert_multiple(result)
        logger.info(f"{rss.name} 第一次抓取成功！")
        return

    pr = ParsingRss(rss=rss)
    await pr.start(rss_name=rss.name, new_rss=new_rss)


async def auto_stop_and_notify_all(rss: Rss) -> None:
    rss.stop = True
    rss.upsert()
    tr.delete_job(rss)
    cookies_str = "及 cookies " if rss.cookies else ""
    msg = (
        f"{rss.name}[{rss.get_url()}]已经连续抓取失败超过 100 次！已自动停止更新！请检查订阅地址{cookies_str}！"
        if rss.error_count >= 100
        else f"{rss.name}[{rss.get_url()}]第一次抓取失败！已自动停止更新！请检查订阅地址或代理设置{cookies_str}！"
    )
    await send_msg(
        rss=rss,
        msg=msg,
        item={},
    )


# 获取 RSS 并解析为 json
async def fetch_rss(rss: Rss) -> Tuple[Dict[str, Any], bool]:
    rss_url = rss.get_url()
    # 对本机部署的 RSSHub 不使用代理
    local_host = [
        "localhost",
        "127.0.0.1",
    ]
    proxy = get_proxy(rss.img_proxy) if URL(rss_url).host not in local_host else None

    # 判断是否使用cookies
    cookies = rss.cookies or None

    # 获取 xml
    d: Dict[str, Any] = {}
    cached = False
    headers = HEADERS.copy()
    if not config.rsshub_backup:
        if rss.etag:
            headers["If-None-Match"] = rss.etag
        if rss.last_modified:
            headers["If-Modified-Since"] = rss.last_modified
    async with aiohttp.ClientSession(
        cookies=cookies,
        headers=HEADERS,
    ) as session:
        try:
            resp = await session.get(rss_url, proxy=proxy)
            if not config.rsshub_backup:
                http_caching_headers = get_http_caching_headers(resp.headers)
                rss.etag = http_caching_headers["ETag"]
                rss.last_modified = http_caching_headers["Last-Modified"]
                rss.upsert()
            if resp.status == 429:
                await asyncio.sleep(randint(1, 5))
                return await fetch_rss(rss)
            if (
                resp.status == 200 and int(resp.headers.get("Content-Length", "1")) == 0
            ) or resp.status == 304:
                cached = True
            # 解析为 JSON
            d = feedparser.parse(await resp.text())
        except Exception:
            if not URL(rss.url).scheme and config.rsshub_backup:
                logger.debug(f"[{rss_url}]访问失败！将使用备用 RSSHub 地址！")
                for rsshub_url in list(config.rsshub_backup):
                    rss_url = rss.get_url(rsshub=rsshub_url)
                    try:
                        resp = await session.get(rss_url, proxy=proxy)
                        d = feedparser.parse(await resp.text())
                    except Exception:
                        logger.debug(f"[{rss_url}]访问失败！将使用备用 RSSHub 地址！")
                        continue
                    if d.get("feed"):
                        logger.info(f"[{rss_url}]抓取成功！")
                        break
    return d, cached
