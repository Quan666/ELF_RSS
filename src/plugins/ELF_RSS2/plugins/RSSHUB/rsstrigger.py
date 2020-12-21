from bot import config
from . import RSS_class, rsshub
from nonebot import require


from nonebot.log import logger

# from RSSHUB import rsshub,RSS_class
from apscheduler.triggers.interval import IntervalTrigger  # 间隔触发器


# 检测某个rss更新 #任务体
async def check_update(rss: RSS_class.rss):
    logger.info('检查 ' + rss.name + ' 更新')
    await rsshub.getRSS(rss)


async def delJob(rss: RSS_class.rss):
    scheduler = require("nonebot_plugin_apscheduler").scheduler
    try:
        scheduler.remove_job(rss.name)
    except Exception as e:
        logger.debug(e)

async def addJob(rss: RSS_class.rss):
    await delJob(rss)
    # 加入订阅任务队列,加入前判断是否存在群组或用户，二者不能同时为空
    if len(rss.user_id)>0 or len(rss.group_id):
        rss_trigger(rss.time, rss)


def rss_trigger(times: int, rss: RSS_class.rss):
    scheduler = require("nonebot_plugin_apscheduler").scheduler
    # 制作一个“time分钟/次”触发器
    trigger = IntervalTrigger(
        minutes=times,
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
