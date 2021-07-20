import codecs
import nonebot
import os
import re
from nonebot import logger, on_metaevent
from nonebot.adapters.cqhttp import Bot, Event, LifecycleMetaEvent
from pathlib import Path

from .config import config
from .RSS import rss_class
from .RSS import my_trigger as rt

FILE_PATH = str(str(Path.cwd()) + os.sep + "data" + os.sep)


def hash_clear():
    json_paths = list(Path(FILE_PATH).glob("*.json"))

    for j in [str(i) for i in json_paths if i != "rss.json"]:

        with codecs.open(j, "r", "utf-8") as f:
            lines = f.readlines()

        with codecs.open(j, "w", "utf-8") as f:
            for line in lines:
                if not re.search(r'"hash": "[0-9a-zA-Z]{32}",', line):
                    f.write(line)


async def start():
    (bot,) = nonebot.get_bots().values()

    try:
        rss = rss_class.Rss("", "", "-1", "-1")
        rss_list = rss.read_rss()  # 读取list
        if not rss_list:
            raise Exception("第一次启动，你还没有订阅，记得添加哟！")
        for rss_tmp in rss_list:
            if not rss_tmp.stop:
                await rt.add_job(rss_tmp)  # 创建检查更新任务
        await bot.send_msg(
            message_type="private",
            user_id=str(list(config.superusers)[0]),
            message=(
                "ELF_RSS 订阅器启动成功！\n"
                f"Version: {config.version}\n"
                "Author：Quan666\n"
                "https://github.com/Quan666/ELF_RSS"
            ),
        )
        logger.info("ELF_RSS 订阅器启动成功！")
        if config.version == "v2.2.7":
            hash_clear()
    except Exception as e:
        await bot.send_msg(
            message_type="private",
            user_id=str(list(config.superusers)[0]),
            message=(
                "第一次启动，你还没有订阅，记得添加哟！\n"
                f"Version: {config.version}\n"
                "Author：Quan666\n"
                "https://github.com/Quan666/ELF_RSS"
            ),
        )
        logger.info("第一次启动，你还没有订阅，记得添加哟！")
        logger.debug(e)


async def check_first_connect(bot: Bot, event: Event, state: dict) -> bool:
    if isinstance(event, LifecycleMetaEvent) and not config.is_start:
        config.is_start = True
        return True
    return False


start_metaevent = on_metaevent(rule=check_first_connect, block=True)


@start_metaevent.handle()
async def _(bot: Bot, event: Event, state: dict):
    # 启动时发送启动成功信息
    await start()
