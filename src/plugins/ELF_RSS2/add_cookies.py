from nonebot import on_command
from nonebot import permission as SUPERUSER
from nonebot.adapters.cqhttp import Bot, Event, permission, unescape
from nonebot.rule import to_me
from .RSS import my_trigger as TR
from .RSS import rss_class

ADD_COOKIES = on_command('addcookies', aliases={'添加cookies'}, rule=to_me(
), priority=5, permission=SUPERUSER.SUPERUSER | permission.GROUP_ADMIN | permission.GROUP_OWNER)


@ADD_COOKIES.handle()
async def handle_first_receive(bot: Bot, event: Event, state: dict):
    args = str(event.message).strip()  # 首次发送命令时跟随的参数，例：/天气 上海，则args为上海
    if args:
        state["ADD_COOKIES"] = unescape(args)  # 如果用户发送了参数则直接赋值


# 如果只有名称就把该 名称订阅 订阅到当前账号或群组


@ADD_COOKIES.got("ADD_COOKIES",
                 prompt="请输入\n名称 cookies\n空格分割\n获取方式：\nPC端 chrome 浏览器按 F12\n找到Consle选项卡，输入:\ndocument.cookie\n输出的字符串就是了")
async def handle_add_cookies(bot: Bot, event: Event, state: dict):
    rss_cookies = unescape(state["ADD_COOKIES"])

    dy = rss_cookies.split(' ', 1)

    rss = rss_class.Rss(name='', url='', user_id='-1', group_id='-1')
    # 判断是否有该名称订阅
    try:
        name = dy[0]
    except ValueError:
        await ADD_COOKIES.send('❌ 输入的订阅名为空！')
        return

    if not rss.find_name(name=name):
        await ADD_COOKIES.send('❌ 不存在该订阅: {}'.format(name))
        return
    rss = rss.find_name(name=name)

    try:
        cookies = dy[1]
    except ValueError:
        await ADD_COOKIES.send('❌ 输入的cookies为空！')
        return

    rss.name = name
    if rss.set_cookies(cookies):
        await TR.add_job(rss)
        await ADD_COOKIES.send('👏 {}的Cookies添加成功！\nCookies:{}\n'.format(rss.name, rss.cookies))
    else:
        await ADD_COOKIES.send('👏 {}的Cookies添加失败！\nCookies:{}\n'.format(rss.name, rss.cookies))
