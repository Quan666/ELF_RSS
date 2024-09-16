import asyncio

from nonebot import on_metaevent, require
from nonebot.adapters.onebot.v11 import Bot, LifecycleMetaEvent
from nonebot.log import logger
from nonebot.plugin import PluginMetadata

require("nonebot_plugin_apscheduler")

from . import command
from . import my_trigger as tr
from .config import DATA_PATH, ELFConfig
from .config import config as plugin_config
from .rss_class import Rss
from .utils import send_message_to_admin

VERSION = "2.6.25"

__plugin_meta__ = PluginMetadata(
    name="ELF_RSS",
    description="QQ机器人 RSS订阅 插件，订阅源建议选择 RSSHub",
    usage="https://github.com/Quan666/ELF_RSS/blob/2.0/docs/2.0%20%E4%BD%BF%E7%94%A8%E6%95%99%E7%A8%8B.md",
    type="application",
    homepage="https://github.com/Quan666/ELF_RSS",
    config=ELFConfig,
    supported_adapters={"~onebot.v11"},
    extra={"author": "Quan666 <i@Rori.eMail>", "version": VERSION},
)


def check_first_connect(_: LifecycleMetaEvent) -> bool:
    return True


start_metaevent = on_metaevent(rule=check_first_connect, temp=True)
FIRST_BOOT_MESSAGE = (
    "首次启动，目前没有订阅，请添加！\n另外，请检查配置文件的内容（详见部署教程）！"
)
BOOT_SUCCESS_MESSAGE = "ELF_RSS 订阅器启动成功！"


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
        await send_message_to_admin(f"{FIRST_BOOT_MESSAGE}\n{boot_message}", bot)
        logger.info(FIRST_BOOT_MESSAGE)
    if plugin_config.enable_boot_message:
        await send_message_to_admin(f"{BOOT_SUCCESS_MESSAGE}\n{boot_message}", bot)
    logger.info(BOOT_SUCCESS_MESSAGE)
    # 创建检查更新任务
    await asyncio.gather(*[tr.add_job(rss) for rss in rss_list if not rss.stop])
