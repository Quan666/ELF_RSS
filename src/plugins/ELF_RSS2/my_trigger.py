import asyncio
import re

from apscheduler.executors.pool import ProcessPoolExecutor, ThreadPoolExecutor
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from nonebot import require
from nonebot.log import logger

from . import rss_parsing
from .rss_class import Rss

wait_for = 5 * 60


# 检测某个rss更新
async def check_update(rss: Rss) -> None:
    logger.info(f"{rss.name} 检查更新")
    try:
        await asyncio.wait_for(rss_parsing.start(rss), timeout=wait_for)
    except asyncio.TimeoutError:
        logger.error(f"{rss.name} 检查更新超时，结束此次任务!")


def delete_job(rss: Rss) -> None:
    scheduler = require("nonebot_plugin_apscheduler").scheduler
    if scheduler.get_job(rss.name):
        scheduler.remove_job(rss.name)


# 加入订阅任务队列并立即执行一次
async def add_job(rss: Rss) -> None:
    delete_job(rss)
    # 加入前判断是否存在子频道或群组或用户，三者不能同时为空
    if any([rss.user_id, rss.group_id, rss.guild_channel_id]):
        rss_trigger(rss)
        await check_update(rss)


def rss_trigger(rss: Rss) -> None:
    if re.search(r"[_*/,-]", rss.time):
        my_trigger_cron(rss)
        return
    scheduler = require("nonebot_plugin_apscheduler").scheduler
    # 制作一个“time分钟/次”触发器
    trigger = IntervalTrigger(
        minutes=int(rss.time), jitter=10, timezone="Asia/Shanghai"
    )
    # 添加任务
    scheduler.add_job(
        func=check_update,  # 要添加任务的函数，不要带参数
        trigger=trigger,  # 触发器
        args=(rss,),  # 函数的参数列表，注意：只有一个值时，不能省略末尾的逗号
        id=rss.name,
        misfire_grace_time=30,  # 允许的误差时间，建议不要省略
        max_instances=1,  # 最大并发
        default=ThreadPoolExecutor(64),  # 最大线程
        processpool=ProcessPoolExecutor(8),  # 最大进程
        coalesce=True,  # 积攒的任务是否只跑一次，是否合并所有错过的Job
    )
    logger.info(f"定时任务 {rss.name} 添加成功")


# cron 表达式
# 参考 https://www.runoob.com/linux/linux-comm-crontab.html


def my_trigger_cron(rss: Rss) -> None:
    # 解析参数
    tmp_list = rss.time.split("_")
    times_list = ["*/5", "*", "*", "*", "*"]
    for index, value in enumerate(tmp_list):
        if value:
            times_list[index] = value
    try:
        # 制作一个触发器
        trigger = CronTrigger(
            minute=times_list[0],
            hour=times_list[1],
            day=times_list[2],
            month=times_list[3],
            day_of_week=times_list[4],
            timezone="Asia/Shanghai",
        )
    except Exception:
        logger.exception(f"创建定时器错误！cron:{times_list}")
        return
    scheduler = require("nonebot_plugin_apscheduler").scheduler

    # 添加任务
    scheduler.add_job(
        func=check_update,  # 要添加任务的函数，不要带参数
        trigger=trigger,  # 触发器
        args=(rss,),  # 函数的参数列表，注意：只有一个值时，不能省略末尾的逗号
        id=rss.name,
        misfire_grace_time=30,  # 允许的误差时间，建议不要省略
        max_instances=1,  # 最大并发
        default=ThreadPoolExecutor(64),  # 最大线程
        processpool=ProcessPoolExecutor(8),  # 最大进程
        coalesce=True,  # 积攒的任务是否只跑一次，是否合并所有错过的Job
    )
    logger.info(f"定时任务 {rss.name} 添加成功")
