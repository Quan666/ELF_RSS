from typing import Any
from ..config import config
import asyncio
from telethon import TelegramClient

from ..config import config

proxy = None
if config.rss_proxy:
    proxy = (
        "http",
        config.rss_proxy.split(":")[0],
        int(config.rss_proxy.split(":")[1]),
    )

bot = None


async def start_tg(loop: Any) -> None:
    global bot
    bot = TelegramClient(
        "bot",
        config.telegram_api_id,
        config.telegram_api_hash,
        proxy=proxy,
        loop=loop,
    )
    if bot:
        from . import telegram_command
    await bot.start(bot_token=config.telegram_bot_token)
