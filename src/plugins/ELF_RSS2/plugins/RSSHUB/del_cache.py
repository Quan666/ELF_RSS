import shutil
from pathlib import Path

import nonebot
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger  # 间隔触发器
from nonebot import logger
from nonebot import require

from bot import config

# scheduler = require("nonebot_plugin_apscheduler").scheduler
scheduler = BackgroundScheduler()
# 图片存储目录
file_path = Path.cwd() / 'data' / 'imgs'


# file_path = './data/imgs'

async def del_img(int):
    bot, = nonebot.get_bots().values()
    try:
        shutil.rmtree(file_path)
        await bot.send_msg(message_type='private', user_id=str(list(config.superusers)[0]), message='图片缓存已经删除！')
    except Exception as e:
        logger.error(e)
        await bot.send_msg(message_type='private', user_id=str(list(config.superusers)[0]), message='图片缓存删除失败！')


def delcache_trigger():
    # 制作一个“time分钟/次”触发器
    trigger = IntervalTrigger(
        days=config.delcache,
        # minutes=1,
        jitter=10
    )
    # 添加任务

    scheduler.add_job(
        func=del_img,  # 要添加任务的函数，不要带参数
        trigger=trigger,  # 触发器
        args=(1,),  # 函数的参数列表，注意：只有一个值时，不能省略末尾的逗号
        id='DELCACHE',
        # kwargs=None,
        misfire_grace_time=60,  # 允许的误差时间，建议不要省略
        # jobstore='default',  # 任务储存库，在下一小节中说明
    )
