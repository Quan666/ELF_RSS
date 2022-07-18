import asyncio
import re

from nonebot import on_command
from nonebot.adapters.onebot.v11 import GroupMessageEvent, Message, MessageEvent
from nonebot.adapters.onebot.v11.permission import GROUP_ADMIN, GROUP_OWNER
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER
from nonebot.rule import to_me
from nonebot_plugin_guild_patch import GuildMessageEvent

from ..permission import GUILD_SUPERUSER
from ..rss_class import Rss
from .show_dy import handle_rss_list

RSS_SHOW_ALL = on_command(
    "show_all",
    aliases={"showall", "select_all", "selectall", "所有订阅"},
    rule=to_me(),
    priority=5,
    permission=GROUP_ADMIN | GROUP_OWNER | GUILD_SUPERUSER | SUPERUSER,
)


@RSS_SHOW_ALL.handle()
async def handle_rss_show_all(
    event: MessageEvent, args: Message = CommandArg()
) -> None:
    search_keyword = args.extract_plain_text().strip()

    group_id = None
    guild_channel_id = None

    if isinstance(event, GroupMessageEvent):
        group_id = event.group_id
    elif isinstance(event, GuildMessageEvent):
        guild_channel_id = f"{event.guild_id}@{event.channel_id}"

    if group_id:
        rss_list = Rss.get_by_group(group_id=group_id)
        if not rss_list:
            await RSS_SHOW_ALL.finish("❌ 当前群组没有任何订阅！")
    elif guild_channel_id:
        rss_list = Rss.get_by_guild_channel(guild_channel_id=guild_channel_id)
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
        await RSS_SHOW_ALL.send(f"当前共有 {len(result)} 条订阅")
        result.sort(key=lambda x: x.get_url())
        await asyncio.sleep(0.5)
        for parted_result in [result[i : i + 30] for i in range(0, len(result), 30)]:
            msg_str = handle_rss_list(parted_result)
            await RSS_SHOW_ALL.send(msg_str)
    else:
        await RSS_SHOW_ALL.finish("❌ 当前没有任何订阅！")
