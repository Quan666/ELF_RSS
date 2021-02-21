import re
import time

from apscheduler.triggers.cron import CronTrigger
from google_trans_new import google_translator
from retrying import retry
from apscheduler.triggers.interval import IntervalTrigger # 间隔触发器
from apscheduler.schedulers.background import BackgroundScheduler

@retry(stop_max_attempt_number=5,stop_max_delay=30*1000)
def testRetry():
    try:
        # print(2)
        raise BaseException
    except BaseException as e:
        print('1')
        raise BaseException

def my_trigger(scheduler,id,times:str,f,argss):
    # 解析参数
    tmp_list = times.split('_')
    times_list=['*/5','*','*','*','*']
    for i in range(0,len(tmp_list)):
        if tmp_list[i]!=None and tmp_list[i]!='':
            times_list[i]=tmp_list[i]
    print(times_list)
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
        print(e)
        return

    job_defaults = {'max_instances': 10}
    # 添加任务
    scheduler.add_job(
        func=f,  # 要添加任务的函数，不要带参数
        trigger=trigger,  # 触发器
        args=argss,  # 函数的参数列表，注意：只有一个值时，不能省略末尾的逗号
        id=id,
        # kwargs=None,
        misfire_grace_time=30,  # 允许的误差时间，建议不要省略
        # jobstore='default',  # 任务储存库，在下一小节中说明
        job_defaults=job_defaults,
    )
def start(scheduler):
    scheduler.start()


def ffc():
    print('run')
    print(time.localtime())


def test2():
    print(time.localtime())
    if re.search('_|\*|/|,|-','*/1'):
        print('yes')
    # 创建定时任务的调度器对象
    scheduler = BackgroundScheduler()
    my_trigger(scheduler,'123','*/1_*/1_*_3_7,2',ffc,())
    start(scheduler)
    time.sleep(10000)

def testtranslator():
    translator = google_translator()
    print(type(translator.translate(re.escape('hello'), lang_tgt='zh')))
def ttt(sss:str=None):
    return

if __name__ == '__main__':
    # testRetry()
    # if None==None or len(None):
    #     pass
    # test2()
    # testtranslator()

    # ttt(sss=None)
    print(time.localtime())
    print(time.time())