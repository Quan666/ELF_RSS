import asyncio

from nonebot import on_metaevent
from nonebot.adapters.onebot.v11 import Bot, LifecycleMetaEvent
from nonebot.log import logger
from nonebot.plugin import PluginMetadata

from . import command
from . import my_trigger as tr
from .config import DATA_PATH, config
from .rss_class import Rss
from .utils import send_message_to_admin

VERSION = "2.6.19"

__plugin_meta__ = PluginMetadata(
    name="ELF_RSS",
    description="QQ机器人 RSS订阅 插件，订阅源建议选择 RSSHub",
    usage="https://github.com/Quan666/ELF_RSS",
    extra={"author": "Quan666 <i@Rori.eMail>", "version": VERSION},
)


def check_first_connect(_: LifecycleMetaEvent) -> bool:
    return True


start_metaevent = on_metaevent(rule=check_first_connect, temp=True)


# 启动时发送启动成功信息
@start_metaevent.handle()
async def start(bot: Bot) -> None:
    # 启动后检查 data 目录，不存在就创建
    if not DATA_PATH.is_dir():
        DATA_PATH.mkdir()

    boot_message = (
        f"Version: v{VERSION}\nAuthor：Quan666\nhttps://github.com/Quan666/ELF_RSS"
    )

    rss_list = Rss.read_rss()  # 读取list
    if not rss_list:
        if config.enable_boot_message:
            await send_message_to_admin(f"第一次启动，你还没有订阅，记得添加哟！\n{boot_message}", bot)
        logger.info("第一次启动，你还没有订阅，记得添加哟！")
    if config.enable_boot_message:
        await send_message_to_admin(f"ELF_RSS 订阅器启动成功！\n{boot_message}", bot)
    logger.info("ELF_RSS 订阅器启动成功！")
    # 创建检查更新任务
    await asyncio.gather(*[tr.add_job(rss) for rss in rss_list if not rss.stop])
