import re

from nonebot import on_command
from nonebot.adapters.onebot.v11 import GroupMessageEvent, Message, MessageEvent
from nonebot.adapters.onebot.v11.permission import GROUP_ADMIN, GROUP_OWNER
from nonebot.matcher import Matcher
from nonebot.params import ArgPlainText, CommandArg
from nonebot.permission import SUPERUSER
from nonebot.rule import to_me
from nonebot_plugin_guild_patch import GuildMessageEvent

from .. import my_trigger as tr
from ..permission import GUILD_SUPERUSER
from ..rss_class import Rss

RSS_ADD = on_command(
    "add",
    aliases={"添加订阅", "sub"},
    rule=to_me(),
    priority=5,
    permission=GROUP_ADMIN | GROUP_OWNER | GUILD_SUPERUSER | SUPERUSER,
)


@RSS_ADD.handle()
async def handle_first_receive(matcher: Matcher, args: Message = CommandArg()) -> None:
    plain_text = args.extract_plain_text().strip()
    if plain_text and re.match(r"^\S+\s\S+$", plain_text):
        matcher.set_arg("RSS_ADD", args)


prompt = """\
请输入
    名称 订阅地址
空格分割
私聊默认订阅到当前账号，群聊默认订阅到当前群组
更多信息可通过 change 命令修改\
"""


@RSS_ADD.got("RSS_ADD", prompt=prompt)
async def handle_rss_add(
    event: MessageEvent, name_and_url: str = ArgPlainText("RSS_ADD")
) -> None:

    try:
        name, url = name_and_url.split(" ")
    except ValueError:
        await RSS_ADD.reject(prompt)
        return

    if _ := Rss.get_one_by_name(name):
        await RSS_ADD.send(f"已存在订阅名为 {name} 的订阅")
        await RSS_ADD.reject(prompt)
        return

    await add_feed(name, url, event)


async def add_feed(
    name: str,
    url: str,
    event: MessageEvent,
) -> None:
    rss = Rss()
    rss.name = name
    rss.url = url
    if isinstance(event, GuildMessageEvent):
        rss.add_user_or_group(
            guild_channel=f"{str(event.guild_id)}@{str(event.channel_id)}"
        )
        await tr.add_job(rss)
        await RSS_ADD.finish("👏 订阅到当前子频道成功！")
    elif isinstance(event, GroupMessageEvent):
        rss.add_user_or_group(group=str(event.group_id))
        await tr.add_job(rss)
        await RSS_ADD.finish("👏 订阅到当前群组成功！")
    else:
        rss.add_user_or_group(user=event.get_user_id())
        await tr.add_job(rss)
        await RSS_ADD.finish("👏 订阅到当前账号成功！")
