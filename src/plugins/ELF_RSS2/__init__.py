import asyncio
import itertools

import arrow
from nonebot import on_metaevent, require
from nonebot.adapters.onebot.v11 import Bot, Event, LifecycleMetaEvent
from nonebot.log import logger
from nonebot.plugin import PluginMetadata
from yarl import URL

from . import command
from . import my_trigger as tr
from .config import DATA_PATH, config
from .rss_class import Rss

VERSION = "2.6.5"
__plugin_meta__ = PluginMetadata(
    name="ELF_RSS",
    description="QQ机器人 RSS订阅 插件，订阅源建议选择 RSSHub",
    usage="https://github.com/Quan666/ELF_RSS",
    extra={"author": "Quan666 <i@Rori.eMail>", "version": VERSION},
)

scheduler = require("nonebot_plugin_apscheduler").scheduler
START_TIME = arrow.now()


async def check_first_connect(event: Event) -> bool:
    return isinstance(event, LifecycleMetaEvent) and arrow.now() < START_TIME.shift(
        minutes=1
    )


start_metaevent = on_metaevent(rule=check_first_connect, block=True)


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
        await bot.send_private_msg(
            user_id=int(list(config.superusers)[0]),
            message=f"第一次启动，你还没有订阅，记得添加哟！\n{boot_message}",
        )
        logger.info("第一次启动，你还没有订阅，记得添加哟！")
    await bot.send_private_msg(
        user_id=int(list(config.superusers)[0]),
        message=f"ELF_RSS 订阅器启动成功！\n{boot_message}",
    )
    logger.info("ELF_RSS 订阅器启动成功！")
    # 创建检查更新任务
    rss_list_group = zip(
        *[
            list(group)
            for key, group in itertools.groupby(
                rss_list, lambda x: URL(x.get_url()).host
            )
        ]
    )
    for _rss_list in rss_list_group:
        await asyncio.gather(*[tr.add_job(rss) for rss in _rss_list if not rss.stop])
