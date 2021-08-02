# -*- coding: UTF-8 -*-

import asyncio
import feedparser
import httpx
import os.path
import re

from nonebot.log import logger
from pathlib import Path
from tenacity import retry, stop_after_attempt, stop_after_delay, RetryError, TryAgain

from . import rss_class
from .routes.Parsing import ParsingRss, get_proxy
from .routes.Parsing.read_or_write_rss_data import read_rss, write_rss
from ..config import config

FILE_PATH = str(str(Path.cwd()) + os.sep + "data" + os.sep)


STATUS_CODE = [200, 301, 302]
# 去掉烦人的 returning true from eof_received() has no effect when using ssl httpx 警告
asyncio.log.logger.setLevel(40)
HEADERS = {
    "Accept": "*/*",
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
    old_rss = read_rss(rss.name)
    old_rss_list = old_rss.get("entries")
    if not old_rss:
        write_rss(name=rss.name, new_rss=new_rss)
        logger.info(f"{rss.name} 第一次抓取成功！")
        return

    pr = ParsingRss(rss=rss)
    await pr.start(new_rss=new_rss, old_data=old_rss_list)


# 获取 RSS 并解析为 json ，失败重试
@retry(stop=(stop_after_attempt(5) | stop_after_delay(30)))
async def get_rss(rss: rss_class.Rss) -> dict:
    # 判断是否使用cookies
    cookies = rss.cookies if rss.cookies else None

    # 获取 xml
    async with httpx.AsyncClient(
        proxies=get_proxy(open_proxy=rss.img_proxy), cookies=cookies, headers=HEADERS
    ) as client:
        d = None
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
                logger.warning(f"RSSHub：[{config.rsshub}]访问失败！将使用备用 RSSHub 地址！")
                for rsshub_url in list(config.rsshub_backup):
                    async with httpx.AsyncClient(
                        proxies=get_proxy(open_proxy=rss.img_proxy)
                    ) as fork_client:
                        try:
                            r = await fork_client.get(rss.get_url(rsshub=rsshub_url))
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
        if not d.get("feed"):
            logger.warning(f"{rss.name} 抓取失败！将重试最多 5 次！")
            raise TryAgain
        return d
