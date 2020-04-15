import logging
from nonebot.log import logger
import datetime
from . import rsshub
from . import RSS_class
from . import RWlist
import nonebot
import asyncio
from apscheduler.triggers.interval import IntervalTrigger # 间隔触发器
from nonebot import on_command, scheduler
import config
import time
# 检测某个rss更新 #任务体
async def check_update(rss:RSS_class.rss):
    logger.info('检查' + rss.name + '更新')
    list = rsshub.getRSS(rss.geturl(), rss.name,rss.img_proxy)
    bot = nonebot.get_bot()
    #await bot.send_msg(message_type=private,user_id=config.ROOTUSER, message='检查更新')
    try:
        if rss.user_id:
            for id in rss.user_id:
                if len(list) > 0:
                    for msg in list:
                        try:
                            await bot.send_msg(message_type='private', user_id=id, message=str(msg))
                        except:
                            logger.info('QQ号不合法或者不是好友')

        if rss.group_id:
            for id in rss.group_id:
                if len(list) > 0:
                    for msg in list:
                        try:
                            await bot.send_msg(message_type='group', group_id=id, message=str(msg))
                        except:
                            logger.info('群号不合法或者未加群')
    except:
        logger.info('发生错误 rsstrigger')



def rss_trigger(times:int,rss:RSS_class.rss):
    # 制作一个“time分钟/次”触发器
    trigger = IntervalTrigger(
        minutes=times,
        jitter=10
    )
    # 添加任务
    scheduler.add_job(
        func=check_update,  # 要添加任务的函数，不要带参数
        trigger=trigger,  # 触发器
        args=(rss,),  # 函数的参数列表，注意：只有一个值时，不能省略末尾的逗号
        id=rss.name,
        # kwargs=None,
        misfire_grace_time=60,  # 允许的误差时间，建议不要省略
        # jobstore='default',  # 任务储存库，在下一小节中说明
    )