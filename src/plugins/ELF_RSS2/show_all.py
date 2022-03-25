import re

from nonebot import on_command
from nonebot.adapters.onebot.v11 import Event, GroupMessageEvent, Message
from nonebot.adapters.onebot.v11.permission import GROUP_ADMIN, GROUP_OWNER
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER
from nonebot.rule import to_me
from nonebot_plugin_guild_patch import GuildMessageEvent

from .permission import GUILD_SUPERUSER
from .RSS.rss_class import Rss
from .show_dy import handle_rss_list

RSS_SHOW_ALL = on_command(
    "show_all",
    aliases={"showall", "select_all", "selectall", "所有订阅"},
    rule=to_me(),
    priority=5,
    permission=GROUP_ADMIN | GROUP_OWNER | GUILD_SUPERUSER | SUPERUSER,
)


@RSS_SHOW_ALL.handle()
async def handle_rss_show_all(event: Event, args: Message = CommandArg()) -> None:
    search_keyword = args.extract_plain_text()

    group_id = None
    guild_channel_id = None

    if isinstance(event, GroupMessageEvent):
        group_id = event.group_id
    elif isinstance(event, GuildMessageEvent):
        guild_channel_id = str(event.guild_id) + "@" + str(event.channel_id)

    if group_id:
        rss_list = Rss.find_group(group=str(group_id))
        if not rss_list:
            await RSS_SHOW_ALL.finish("❌ 当前群组没有任何订阅！")
    elif guild_channel_id:
        rss_list = Rss.find_guild_channel(guild_channel=guild_channel_id)
        if not rss_list:
            await RSS_SHOW_ALL.finish("❌ 当前子频道没有任何订阅！")
    else:
        rss_list = Rss.read_rss()

    result = []
    if search_keyword:
        for i in rss_list:
            test = bool(
                re.search(search_keyword, i.name, flags=re.I)
                or re.search(search_keyword, i.url, flags=re.I)
            )
            if not group_id and not guild_channel_id and search_keyword.isdigit():
                if i.user_id:
                    test = test or search_keyword in i.user_id
                if i.group_id:
                    test = test or search_keyword in i.group_id
                if i.guild_channel_id:
                    test = test or search_keyword in i.guild_channel_id
            if test:
                result.append(i)
    else:
        result = rss_list

    if result:
        msg_str = await handle_rss_list(result)
        await RSS_SHOW_ALL.finish(msg_str)
    else:
        await RSS_SHOW_ALL.finish("❌ 当前没有任何订阅！")
