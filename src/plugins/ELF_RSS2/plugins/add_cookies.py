import re

from RSSHUB import RSS_class, RWlist, rsstrigger as TR
from nonebot import on_command
from nonebot.adapters.cqhttp import permission, unescape
from nonebot import permission as SUPERUSER
from nonebot.adapters.cqhttp import Bot, Event
from nonebot.log import logger
from nonebot.rule import to_me

from bot import config

Addcookies = on_command('addcookies', aliases={'添加cookies'}, rule=to_me(), priority=5, permission=SUPERUSER.SUPERUSER|permission.GROUP_ADMIN)


@Addcookies.handle()
async def handle_first_receive(bot: Bot, event: Event, state: dict):
    args = str(event.message).strip()  # 首次发送命令时跟随的参数，例：/天气 上海，则args为上海
    if args:
        state["Addcookies"] = unescape(args)  # 如果用户发送了参数则直接赋值

# 如果只有名称就把该 名称订阅 订阅到当前账号或群组
@Addcookies.got("Addcookies",
            prompt="请输入\n名称 cookies\n空格分割\n获取方式：\nPC端 chrome 浏览器按 F12\n找到Consle选项卡，输入:\ndocument.cookie\n输出的字符串就是了")
async def handle_Addcookies(bot: Bot, event: Event, state: dict):
    rss_cookies = state["Addcookies"]

    dy = rss_cookies.split(' ',1)

    rss = RSS_class.rss(name='',url='',user_id='-1',group_id='-1')
    # 判断是否有该名称订阅
    try:
        name = dy[0]
    except:
        await Addcookies.send('❌ 输入的订阅名为空！')
        return

    if not rss.findName(name=name):
        await Addcookies.send('❌ 不存在该订阅: {}'.format(name))
        return
    rss = rss.findName(name=name)

    try:
        cookies = dy[1]
    except:
        await Addcookies.send('❌ 输入的cookies为空！')
        return

    rss.name=name
    if rss.setCookies(cookies):
        await Addcookies.send('👏 {}的Cookies添加成功！\nCookies:{}\n'.format(rss.name,rss.cookies))
    else:
        await Addcookies.send('👏 {}的Cookies添加失败！\nCookies:{}\n'.format(rss.name,rss.cookies))
