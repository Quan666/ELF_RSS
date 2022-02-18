from nonebot import on_command
from nonebot.adapters.onebot.v11 import Message
from nonebot.adapters.onebot.v11.permission import GROUP_ADMIN, GROUP_OWNER
from nonebot.matcher import Matcher
from nonebot.params import ArgPlainText, CommandArg
from nonebot.permission import SUPERUSER
from nonebot.rule import to_me

from .RSS import my_trigger as tr
from .RSS import rss_class

ADD_COOKIES = on_command(
    "add_cookies",
    aliases={"添加cookies"},
    rule=to_me(),
    priority=5,
    permission=GROUP_ADMIN | GROUP_OWNER | SUPERUSER,
)


@ADD_COOKIES.handle()
async def handle_first_receive(matcher: Matcher, args: Message = CommandArg()):
    plain_text = args.extract_plain_text()
    if plain_text:
        matcher.set_arg("COOKIES", args)


prompt = """\
请输入：
    名称 cookies
空格分割

获取方式：
    PC端 Chrome 浏览器按 F12
    找到Console选项卡，输入:
        document.cookie
    输出的字符串就是了\
"""


@ADD_COOKIES.got("COOKIES", prompt=prompt)
async def handle_add_cookies(rss_cookies: str = ArgPlainText("COOKIES")):
    dy = rss_cookies.split(" ", 1)

    rss = rss_class.Rss()
    # 判断是否有该名称订阅
    try:
        name = dy[0]
    except IndexError:
        await ADD_COOKIES.finish("❌ 输入的订阅名为空！")

    rss = rss.find_name(name=name)

    if rss is None:
        await ADD_COOKIES.finish(f"❌ 不存在该订阅: {name}")
    else:
        try:
            cookies = dy[1]
        except IndexError:
            await ADD_COOKIES.finish("❌ 输入的cookies为空！")

        rss.name = name
        if rss.set_cookies(cookies):
            await tr.add_job(rss)
            await ADD_COOKIES.finish(
                f"👏 {rss.name}的Cookies添加成功！\nCookies:{rss.cookies}\n"
            )
        else:
            await ADD_COOKIES.finish(
                f"❌ {rss.name}的Cookies添加失败！\nCookies:{rss.cookies}\n"
            )
