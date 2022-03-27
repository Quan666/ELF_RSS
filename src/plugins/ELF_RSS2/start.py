import arrow
import nonebot
from nonebot import on_metaevent, require
from nonebot.adapters.onebot.v11 import Event, LifecycleMetaEvent
from nonebot.log import logger

from .config import DATA_PATH, config
from .RSS import my_trigger as tr
from .RSS.rss_class import Rss

scheduler = require("nonebot_plugin_apscheduler").scheduler
START_TIME = arrow.now()


async def check_first_connect(event: Event) -> bool:
    return isinstance(event, LifecycleMetaEvent) and arrow.now() < START_TIME.shift(
        minutes=1
    )


start_metaevent = on_metaevent(rule=check_first_connect, block=True)


# 启动时发送启动成功信息
@start_metaevent.handle()
async def start() -> None:
    bot = nonebot.get_bot()

    # 启动后检查 data 目录，不存在就创建
    if not DATA_PATH.is_dir():
        DATA_PATH.mkdir()

    boot_message = (
        f"Version: {config.version}\n"
        "Author：Quan666\n"
        "https://github.com/Quan666/ELF_RSS"
    )

    rss_list = Rss.read_rss()  # 读取list
    if not rss_list:
        await bot.send_private_msg(
            user_id=int(list(config.superusers)[0]),
            message=f"第一次启动，你还没有订阅，记得添加哟！\n{boot_message}",
        )
        logger.info("第一次启动，你还没有订阅，记得添加哟！")
    # 创建检查更新任务
    for rss_tmp in rss_list:
        if not rss_tmp.stop:
            tr.add_job(rss_tmp)
    await bot.send_private_msg(
        user_id=int(list(config.superusers)[0]),
        message=f"ELF_RSS 订阅器启动成功！\n{boot_message}",
    )
    logger.info("ELF_RSS 订阅器启动成功！")
