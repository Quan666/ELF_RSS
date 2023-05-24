from typing import List, Optional

from nonebot import on_command
from nonebot.adapters.onebot.v11 import GroupMessageEvent, Message, MessageEvent
from nonebot.adapters.onebot.v11.permission import GROUP_ADMIN, GROUP_OWNER
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER
from nonebot.rule import to_me

from ..permission import GUILD_SUPERUSER
from ..rss_class import Rss
from ..utils import GUILD_ADMIN, GUILD_OWNER, GuildMessageEvent

RSS_SHOW = on_command(
    "show",
    aliases={"查看订阅"},
    rule=to_me(),
    priority=5,
    permission=GROUP_ADMIN
    | GROUP_OWNER
    | GUILD_ADMIN
    | GUILD_OWNER
    | GUILD_SUPERUSER
    | SUPERUSER,
)


def handle_rss_list(rss_list: List[Rss]) -> str:
    rss_info_list = [
        f"（已停止）{i.name}：{i.url}" if i.stop else f"{i.name}：{i.url}" for i in rss_list
    ]
    return "\n\n".join(rss_info_list)


async def show_rss_by_name(
    rss_name: str, group_id: Optional[int], guild_channel_id: Optional[str]
) -> str:
    rss = Rss.get_one_by_name(rss_name)
    if (
        rss is None
        or (group_id and str(group_id) not in rss.group_id)
        or (guild_channel_id and guild_channel_id not in rss.guild_channel_id)
    ):
        return f"❌ 订阅 {rss_name} 不存在或未订阅！"
    else:
        # 隐私考虑，不展示除当前群组或频道外的群组、频道和QQ
        return str(rss.hide_some_infos(group_id, guild_channel_id))


# 不带订阅名称默认展示当前群组或账号的订阅，带订阅名称就显示该订阅的
@RSS_SHOW.handle()
async def handle_rss_show(event: MessageEvent, args: Message = CommandArg()) -> None:
    rss_name = args.extract_plain_text().strip()

    user_id = event.get_user_id()
    group_id = event.group_id if isinstance(event, GroupMessageEvent) else None
    guild_channel_id = (
        f"{event.guild_id}@{event.channel_id}"
        if isinstance(event, GuildMessageEvent)
        else None
    )

    if rss_name:
        rss_msg = await show_rss_by_name(rss_name, group_id, guild_channel_id)
        await RSS_SHOW.finish(rss_msg)

    if group_id:
        rss_list = Rss.get_by_group(group_id=group_id)
    elif guild_channel_id:
        rss_list = Rss.get_by_guild_channel(guild_channel_id=guild_channel_id)
    else:
        rss_list = Rss.get_by_user(user=user_id)

    if rss_list:
        msg_str = handle_rss_list(rss_list)
        await RSS_SHOW.finish(msg_str)
    else:
        await RSS_SHOW.finish("❌ 当前没有任何订阅！")
