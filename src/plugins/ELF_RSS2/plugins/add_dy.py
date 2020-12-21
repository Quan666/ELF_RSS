import re

from RSSHUB import RSS_class, RWlist, rsstrigger as TR
from nonebot import on_command, permission
from nonebot.adapters.cqhttp import Bot, Event
from nonebot.log import logger
from nonebot.rule import to_me

from bot import config

RssAdd = on_command('add', aliases={'添加订阅', 'sub'}, rule=to_me(), priority=5, permission=permission.SUPERUSER|permission.GROUP_ADMIN)


@RssAdd.handle()
async def handle_first_receive(bot: Bot, event: Event, state: dict):
    args = str(event.message).strip()  # 首次发送命令时跟随的参数，例：/天气 上海，则args为上海
    if args:
        state["RssAdd"] = args  # 如果用户发送了参数则直接赋值

# 如果只有名称就把该 名称订阅 订阅到当前账号或群组
@RssAdd.got("RssAdd",
            prompt="请输入\n名称 [订阅地址]\n空格分割、[]表示可选\n私聊默认订阅到当前账号，群聊默认订阅到当前群组\n更多信息可通过 change 命令修改")
async def handle_RssAdd(bot: Bot, event: Event, state: dict):
    rss_dy_link = state["RssAdd"]
    user_id = event.user_id
    try:
        group_id = event.group_id
    except:
        group_id = None

    dy = rss_dy_link.split(' ')

    rss = RSS_class.rss(name='',url='',user_id='-1',group_id='-1')
    # 判断是否有该名称订阅，有就将当前qq或群加入订阅
    try:
        name = dy[0]
    except:
        await RssAdd.send('输入的订阅名为空！')
        return

    if rss.findName(name=name):
        rss = rss.findName(name=name)
        if group_id:
            rss.addGroup(group=group_id)
            await TR.addJob(rss)
            await RssAdd.send('订阅到当前群组成功！')
        else:
            rss.addUser(user=user_id)
            await TR.addJob(rss)
            await RssAdd.send('订阅到当前账号成功！')
        return

    try:
        url = dy[1]
    except:
        await RssAdd.send('输入的订阅地址为空！')
        return

    # 判断当前订阅地址存在否
    if rss.findURL(url=url):
        rss = rss.findURL(url=url)
        if group_id:
            rss.addGroup(group=group_id)
            await TR.addJob(rss)
            await RssAdd.send('订阅到当前群组成功！')
        else:
            rss.addUser(user=user_id)
            await TR.addJob(rss)
            await RssAdd.send('订阅到当前账号成功！')
        return

    # 当前名称、url都不存在
    rss.name=name
    rss.url=url
    print(rss.geturl())
    if group_id:
        rss.addGroup(group=group_id)
        await TR.addJob(rss)
        await RssAdd.send('订阅到当前群组成功！')
    else:
        rss.addUser(user=user_id)
        await TR.addJob(rss)
        await RssAdd.send('订阅到当前账号成功！')