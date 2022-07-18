import re

from nonebot import on_command
from nonebot.adapters.onebot.v11 import (
    GroupMessageEvent,
    Message,
    MessageEvent,
    PrivateMessageEvent,
)
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
        await RSS_ADD.finish(f"已存在订阅名为 {name} 的订阅")
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
    user = event.user_id if isinstance(event, PrivateMessageEvent) else None
    group = event.group_id if isinstance(event, GroupMessageEvent) else None
    guild_channel = (
        f"{str(event.guild_id)}@{str(event.channel_id)}"
        if isinstance(event, GuildMessageEvent)
        else None
    )
    rss.add_user_or_group_or_channel(str(user), str(group), guild_channel)
    await RSS_ADD.send(f"👏 已成功添加订阅 {name} ！")
    await tr.add_job(rss)
