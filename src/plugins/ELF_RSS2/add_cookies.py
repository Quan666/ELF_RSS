from nonebot import on_command
from nonebot.adapters.onebot.v11 import Message, unescape
from nonebot.adapters.onebot.v11.permission import GROUP_ADMIN, GROUP_OWNER
from nonebot.params import CommandArg, State
from nonebot.permission import SUPERUSER
from nonebot.rule import to_me
from nonebot.typing import T_State

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
async def handle_first_receive(
    message: Message = CommandArg(), state: T_State = State()
):
    args = str(message).strip()
    if args:
        state["COOKIES"] = unescape(args)


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
async def handle_add_cookies(state: T_State = State()):
    rss_cookies = unescape(str(state["COOKIES"]))

    dy = rss_cookies.split(" ", 1)

    rss = rss_class.Rss()
    # 判断是否有该名称订阅
    try:
        name = dy[0]
    except IndexError:
        await ADD_COOKIES.finish("❌ 输入的订阅名为空！")

    if not rss.find_name(name=name):
        await ADD_COOKIES.finish(f"❌ 不存在该订阅: {name}")

    rss = rss.find_name(name=name)

    try:
        cookies = dy[1]
    except IndexError:
        await ADD_COOKIES.finish("❌ 输入的cookies为空！")

    rss.name = name
    if rss.set_cookies(cookies):
        await tr.add_job(rss)
        await ADD_COOKIES.finish(f"👏 {rss.name}的Cookies添加成功！\nCookies:{rss.cookies}\n")
    else:
        await ADD_COOKIES.finish(f"❌ {rss.name}的Cookies添加失败！\nCookies:{rss.cookies}\n")
