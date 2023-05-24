from typing import List, Optional, Tuple

from nonebot import on_command
from nonebot.adapters.onebot.v11 import GroupMessageEvent, Message, MessageEvent
from nonebot.adapters.onebot.v11.permission import GROUP_ADMIN, GROUP_OWNER
from nonebot.matcher import Matcher
from nonebot.params import ArgPlainText, CommandArg
from nonebot.permission import SUPERUSER
from nonebot.rule import to_me

from .. import my_trigger as tr
from ..permission import GUILD_SUPERUSER
from ..rss_class import Rss
from ..utils import GUILD_ADMIN, GUILD_OWNER, GuildMessageEvent

RSS_DELETE = on_command(
    "deldy",
    aliases={"drop", "unsub", "删除订阅"},
    rule=to_me(),
    priority=5,
    permission=GROUP_ADMIN
    | GROUP_OWNER
    | GUILD_ADMIN
    | GUILD_OWNER
    | GUILD_SUPERUSER
    | SUPERUSER,
)


@RSS_DELETE.handle()
async def handle_first_receive(matcher: Matcher, args: Message = CommandArg()) -> None:
    if args.extract_plain_text():
        matcher.set_arg("RSS_DELETE", args)


async def process_rss_deletion(
    rss_name_list: List[str], group_id: Optional[int], guild_channel_id: Optional[str]
) -> Tuple[List[str], List[str]]:
    delete_successes = []
    delete_failures = []

    for rss_name in rss_name_list:
        rss = Rss.get_one_by_name(name=rss_name)
        if rss is None:
            delete_failures.append(rss_name)
        elif guild_channel_id:
            if rss.delete_guild_channel(guild_channel=guild_channel_id):
                if not any([rss.group_id, rss.user_id, rss.guild_channel_id]):
                    rss.delete_rss()
                    tr.delete_job(rss)
                else:
                    await tr.add_job(rss)
                delete_successes.append(rss_name)
            else:
                delete_failures.append(rss_name)
        elif group_id:
            if rss.delete_group(group=str(group_id)):
                if not any([rss.group_id, rss.user_id, rss.guild_channel_id]):
                    rss.delete_rss()
                    tr.delete_job(rss)
                else:
                    await tr.add_job(rss)
                delete_successes.append(rss_name)
            else:
                delete_failures.append(rss_name)
        else:
            rss.delete_rss()
            tr.delete_job(rss)
            delete_successes.append(rss_name)

    return delete_successes, delete_failures


@RSS_DELETE.got("RSS_DELETE", prompt="输入要删除的订阅名")
async def handle_rss_delete(
    event: MessageEvent, rss_name: str = ArgPlainText("RSS_DELETE")
) -> None:
    group_id = event.group_id if isinstance(event, GroupMessageEvent) else None
    guild_channel_id = (
        f"{event.guild_id}@{event.channel_id}"
        if isinstance(event, GuildMessageEvent)
        else None
    )

    rss_name_list = rss_name.strip().split(" ")

    delete_successes, delete_failures = await process_rss_deletion(
        rss_name_list, group_id, guild_channel_id
    )

    result = []
    if delete_successes:
        if guild_channel_id:
            result.append(f'👏 当前子频道成功取消订阅： {"、".join(delete_successes)} ！')
        elif group_id:
            result.append(f'👏 当前群组成功取消订阅： {"、".join(delete_successes)} ！')
        else:
            result.append(f'👏 成功删除订阅： {"、".join(delete_successes)} ！')
    if delete_failures:
        if guild_channel_id:
            result.append(f'❌ 当前子频道没有订阅： {"、".join(delete_successes)} ！')
        elif group_id:
            result.append(f'❌ 当前群组没有订阅： {"、".join(delete_successes)} ！')
        else:
            result.append(f'❌ 未找到订阅： {"、".join(delete_successes)} ！')

    await RSS_DELETE.finish("\n".join(result))
