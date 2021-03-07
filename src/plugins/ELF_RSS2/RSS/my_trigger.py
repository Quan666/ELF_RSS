import re

from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger  # 间隔触发器
from nonebot import require
from nonebot.log import logger

from . import rss_class, rss_parsing


# 检测某个rss更新 #任务体
async def check_update(rss: rss_class.rss):
    logger.info('检查 ' + rss.name + ' 更新')
    await rss_parsing.start(rss)


async def delJob(rss: rss_class.rss):
    scheduler = require("nonebot_plugin_apscheduler").scheduler
    try:
        scheduler.remove_job(rss.name)
    except Exception as e:
        logger.debug(e)


async def addJob(rss: rss_class.rss):
    await delJob(rss)
    # 加入订阅任务队列,加入前判断是否存在群组或用户，二者不能同时为空
    if len(rss.user_id) > 0 or len(rss.group_id) > 0:
        rss_trigger(rss)


def rss_trigger(rss: rss_class.rss):
    if re.search('_|\*|/|,|-', rss.time):
        my_trigger_cron(rss)
        return
    scheduler = require("nonebot_plugin_apscheduler").scheduler
    # 制作一个“time分钟/次”触发器
    trigger = IntervalTrigger(
        minutes=int(rss.time),
        jitter=10
    )
    job_defaults = {'max_instances': 10}
    # 添加任务
    scheduler.add_job(
        func=check_update,  # 要添加任务的函数，不要带参数
        trigger=trigger,  # 触发器
        args=(rss,),  # 函数的参数列表，注意：只有一个值时，不能省略末尾的逗号
        id=rss.name,
        # kwargs=None,
        misfire_grace_time=60,  # 允许的误差时间，建议不要省略
        # jobstore='default',  # 任务储存库，在下一小节中说明
        job_defaults=job_defaults,
    )
    logger.info('定时任务 {} 添加成功'.format(rss.name))

# cron 表达式
# 参考 https://www.runoob.com/linux/linux-comm-crontab.html


def my_trigger_cron(rss: rss_class.rss):
    # 解析参数
    tmp_list = rss.time.split('_')
    times_list = ['*/5', '*', '*', '*', '*']
    for i in range(0, len(tmp_list)):
        if tmp_list[i] != None and tmp_list[i] != '':
            times_list[i] = tmp_list[i]
    try:
        # 制作一个触发器
        trigger = CronTrigger(
            minute=times_list[0],
            hour=times_list[1],
            day=times_list[2],
            month=times_list[3],
            day_of_week=times_list[4],
            timezone='Asia/Shanghai'
        )
    except Exception as e:
        logger.error('创建定时器错误！cron:{} E：{}'.format(times_list, e))
        return

    job_defaults = {'max_instances': 10}
    scheduler = require("nonebot_plugin_apscheduler").scheduler
    # 添加任务
    scheduler.add_job(
        func=check_update,  # 要添加任务的函数，不要带参数
        trigger=trigger,  # 触发器
        args=(rss,),  # 函数的参数列表，注意：只有一个值时，不能省略末尾的逗号
        id=rss.name,
        # kwargs=None,
        misfire_grace_time=60,  # 允许的误差时间，建议不要省略
        # jobstore='default',  # 任务储存库，在下一小节中说明
        job_defaults=job_defaults,
    )
    logger.info('定时任务 {} 添加成功'.format(rss.name))
