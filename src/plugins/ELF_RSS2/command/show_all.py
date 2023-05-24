import asyncio
import re
from typing import List, Optional

from nonebot import on_command
from nonebot.adapters.onebot.v11 import (
    ActionFailed,
    GroupMessageEvent,
    Message,
    MessageEvent,
)
from nonebot.adapters.onebot.v11.permission import GROUP_ADMIN, GROUP_OWNER
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER
from nonebot.rule import to_me

from ..permission import GUILD_SUPERUSER
from ..rss_class import Rss
from ..utils import GUILD_ADMIN, GUILD_OWNER, GuildMessageEvent
from .show_dy import handle_rss_list

RSS_SHOW_ALL = on_command(
    "show_all",
    aliases={"showall", "select_all", "selectall", "所有订阅"},
    rule=to_me(),
    priority=5,
    permission=GROUP_ADMIN
    | GROUP_OWNER
    | GUILD_ADMIN
    | GUILD_OWNER
    | GUILD_SUPERUSER
    | SUPERUSER,
)


def filter_results_by_keyword(
    rss_list: List[Rss],
    search_keyword: str,
    group_id: Optional[int],
    guild_channel_id: Optional[str],
) -> List[Rss]:
    return [
        i
        for i in rss_list
        if (
            re.search(search_keyword, i.name, flags=re.I)
            or re.search(search_keyword, i.url, flags=re.I)
            or (
                search_keyword.isdigit()
                and not group_id
                and not guild_channel_id
                and (
                    (i.user_id and search_keyword in i.user_id)
                    or (i.group_id and search_keyword in i.group_id)
                    or (i.guild_channel_id and search_keyword in i.guild_channel_id)
                )
            )
        )
    ]


def get_rss_list(group_id: Optional[int], guild_channel_id: Optional[str]) -> List[Rss]:
    if group_id:
        return Rss.get_by_group(group_id=group_id)
    elif guild_channel_id:
        return Rss.get_by_guild_channel(guild_channel_id=guild_channel_id)
    else:
        return Rss.read_rss()


@RSS_SHOW_ALL.handle()
async def handle_rss_show_all(
    event: MessageEvent, args: Message = CommandArg()
) -> None:
    search_keyword = args.extract_plain_text().strip()

    group_id = event.group_id if isinstance(event, GroupMessageEvent) else None
    guild_channel_id = (
        f"{event.guild_id}@{event.channel_id}"
        if isinstance(event, GuildMessageEvent)
        else None
    )

    if not (rss_list := get_rss_list(group_id, guild_channel_id)):
        await RSS_SHOW_ALL.finish("❌ 当前没有任何订阅！")
        return

    result = (
        filter_results_by_keyword(rss_list, search_keyword, group_id, guild_channel_id)
        if search_keyword
        else rss_list
    )

    if result:
        await RSS_SHOW_ALL.send(f"当前共有 {len(result)} 条订阅")
        result.sort(key=lambda x: x.get_url())
        await asyncio.sleep(0.5)
        page_size = 30
        while result:
            current_page = result[:page_size]
            msg_str = handle_rss_list(current_page)
            try:
                await RSS_SHOW_ALL.send(msg_str)
            except ActionFailed:
                page_size -= 5
                continue
            result = result[page_size:]
    else:
        await RSS_SHOW_ALL.finish("❌ 当前没有任何订阅！")
