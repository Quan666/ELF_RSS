import nonebot
from nonebot import logger, on_metaevent
from nonebot.adapters.cqhttp import Bot, Event

from .config import config
from .RSS import rss_class
from .RSS import delete_cache as DC
from .RSS import my_trigger as RT


async def start():
    bot, = nonebot.get_bots().values()
    try:
        DC.delcache_trigger()
    except:
        pass

    try:
        rss = rss_class.rss('', '', '-1', '-1')
        rss_list = rss.readRss()  # 读取list
        if not rss_list:
            raise Exception('第一次启动，你还没有订阅，记得添加哟！')
        for rss_tmp in rss_list:
            await RT.addJob(rss_tmp)  # 创建检查更新任务
        await bot.send_msg(message_type='private', user_id=str(list(config.superusers)[0]),
                           message='ELF_RSS 订阅器启动成功！\nVersion: {}\nAuthor：Quan666\nhttps://github.com/Quan666/ELF_RSS'.format(
                               config.version))
        logger.info('ELF_RSS 订阅器启动成功！')
    except Exception as e:
        await bot.send_msg(message_type='private', user_id=str(list(config.superusers)[0]),
                           message='第一次启动，你还没有订阅，记得添加哟！\nVersion: {}\nAuthor：Quan666\nhttps://github.com/Quan666/ELF_RSS'.format(
                               config.version))
        logger.info('第一次启动，你还没有订阅，记得添加哟！')
        logger.debug(e)


async def check_first_connect(bot: Bot, event: Event, state: dict) -> bool:
    if event.meta_event_type == 'lifecycle' and not config.is_start:
        config.is_start=True
        return True
    return False


start_metaevent = on_metaevent(rule=check_first_connect, block=True)


@start_metaevent.handle()
async def _(bot: Bot, event: Event, state: dict):
    """ 启动时发送启动成功信息 """
    await start()
