from typing import Optional

from nonebot import on_command
from nonebot.adapters.onebot.v11 import Event, GroupMessageEvent, Message
from nonebot.adapters.onebot.v11.permission import GROUP_ADMIN, GROUP_OWNER
from nonebot.matcher import Matcher
from nonebot.params import ArgPlainText, CommandArg
from nonebot.permission import SUPERUSER
from nonebot.rule import to_me
from nonebot_plugin_guild_patch import GuildMessageEvent

from .permission import GUILD_SUPERUSER
from .RSS import my_trigger as tr
from .RSS.rss_class import Rss

RSS_ADD = on_command(
    "add",
    aliases={"添加订阅", "sub"},
    rule=to_me(),
    priority=5,
    permission=GROUP_ADMIN | GROUP_OWNER | GUILD_SUPERUSER | SUPERUSER,
)


@RSS_ADD.handle()
async def handle_first_receive(matcher: Matcher, args: Message = CommandArg()) -> None:
    plain_text = args.extract_plain_text()
    if plain_text:
        matcher.set_arg("RSS_ADD", args)


prompt = """\
请输入
    名称 [订阅地址]
空格分割、[]表示可选
私聊默认订阅到当前账号，群聊默认订阅到当前群组
更多信息可通过 change 命令修改\
"""


@RSS_ADD.got("RSS_ADD", prompt=prompt)
async def handle_rss_add(
    event: Event, rss_dy_link: str = ArgPlainText("RSS_ADD")
) -> None:
    user_id = event.get_user_id()
    group_id = None
    guild_channel_id = None

    if isinstance(event, GroupMessageEvent):
        group_id = event.group_id
    elif isinstance(event, GuildMessageEvent):
        guild_channel_id = str(event.guild_id) + "@" + str(event.channel_id)

    dy = rss_dy_link.split(" ")
    name = dy[0]

    rss = Rss()

    async def add_group_or_user(
        _rss: Rss,
        _group_id: Optional[int],
        _user_id: Optional[str],
        _guild_channel_id: Optional[str],
    ) -> None:
        if _guild_channel_id:
            _rss.add_user_or_group(guild_channel=_guild_channel_id)
            tr.add_job(_rss)
            await RSS_ADD.finish("👏 订阅到当前子频道成功！")
        elif _group_id:
            _rss.add_user_or_group(group=str(_group_id))
            tr.add_job(_rss)
            await RSS_ADD.finish("👏 订阅到当前群组成功！")
        else:
            _rss.add_user_or_group(user=_user_id)
            tr.add_job(_rss)
            await RSS_ADD.finish("👏 订阅到当前账号成功！")

    # 判断是否有该名称订阅，有就将当前qq或群加入订阅
    rss_tmp = rss.find_name(name=name)
    if rss_tmp is not None:
        await add_group_or_user(rss_tmp, group_id, user_id, guild_channel_id)
    else:
        # 当前名称、url都不存在
        rss.name = name
        try:
            url = dy[1]
            rss.url = url
            await add_group_or_user(rss, group_id, user_id, guild_channel_id)
        except IndexError:
            await RSS_ADD.finish("❌ 输入的订阅地址为空！")
