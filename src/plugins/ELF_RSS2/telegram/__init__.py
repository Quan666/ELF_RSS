from telethon import TelegramClient

from ..config import config

proxy = None
if config.rss_proxy:
    proxy = (
        "http",
        config.rss_proxy.split(":")[0],
        int(config.rss_proxy.split(":")[1]),
    )

bot = TelegramClient(
    "bot",
    config.telegram_api_id,
    config.telegram_api_hash,
    proxy=proxy,
)
