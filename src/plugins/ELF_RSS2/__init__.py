import asyncio

from nonebot import get_driver, on_metaevent, require
from nonebot.adapters.onebot.v11 import Bot, LifecycleMetaEvent
from nonebot.drivers import Driver
from nonebot.log import logger
from nonebot.plugin import PluginMetadata

from . import command
from . import my_trigger as tr
from .config import DATA_PATH, config
from .rss_class import Rss
from .telegram import start_telegram_bot
from .utils import send_message_to_admin

VERSION = "2.7.0"
__plugin_meta__ = PluginMetadata(
    name="ELF_RSS",
    description="QQ机器人 RSS订阅 插件，订阅源建议选择 RSSHub",
    usage="https://github.com/Quan666/ELF_RSS",
    extra={"author": "Quan666 <i@Rori.eMail>", "version": VERSION},
)

scheduler = require("nonebot_plugin_apscheduler").scheduler


async def check_first_connect(_: LifecycleMetaEvent) -> bool:
    return True


start_metaevent = on_metaevent(rule=check_first_connect, temp=True)


def get_boot_message() -> str:
    boot_message = (
        f"Version: v{VERSION}\nAuthor：Quan666\nhttps://github.com/Quan666/ELF_RSS"
    )
    rss_list = Rss.read_rss()  # 读取list
    if not rss_list:
        logger.info("第一次启动，你还没有订阅，记得添加哟！")
        return f"第一次启动，你还没有订阅，记得添加哟！\n{boot_message}"
    return f"ELF_RSS 订阅器启动成功！\n{boot_message}"


# 启动时发送启动成功信息
@start_metaevent.handle()
async def _(bot: Bot) -> None:

    # 启动后检查 data 目录，不存在就创建
    if not DATA_PATH.is_dir():
        DATA_PATH.mkdir()
    rss_list = Rss.read_rss()  # 读取list
    await send_message_to_admin(get_boot_message(), bot)
    logger.info("ELF_RSS 订阅器启动成功！")
    # 创建检查更新任务
    await asyncio.gather(*[tr.add_job(rss) for rss in rss_list if not rss.stop])


driver: Driver = get_driver()


@driver.on_startup
async def on_startup_telegram_bot() -> None:
    await asyncio.gather(
        start_telegram_bot(asyncio.get_event_loop(), get_boot_message()),
    )
