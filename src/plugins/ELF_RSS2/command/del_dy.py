from nonebot import on_command
from nonebot.adapters.onebot.v11 import Event, GroupMessageEvent, Message
from nonebot.adapters.onebot.v11.permission import GROUP_ADMIN, GROUP_OWNER
from nonebot.matcher import Matcher
from nonebot.params import ArgPlainText, CommandArg
from nonebot.permission import SUPERUSER
from nonebot.rule import to_me
from nonebot_plugin_guild_patch import GuildMessageEvent

from .. import my_trigger as tr
from ..permission import GUILD_SUPERUSER
from ..rss_class import Rss

RSS_DELETE = on_command(
    "deldy",
    aliases={"drop", "删除订阅"},
    rule=to_me(),
    priority=5,
    permission=GROUP_ADMIN | GROUP_OWNER | GUILD_SUPERUSER | SUPERUSER,
)


@RSS_DELETE.handle()
async def handle_first_receive(matcher: Matcher, args: Message = CommandArg()) -> None:
    if args.extract_plain_text():
        matcher.set_arg("RSS_DELETE", args)


@RSS_DELETE.got("RSS_DELETE", prompt="输入要删除的订阅名")
async def handle_rss_delete(
    event: Event, rss_name: str = ArgPlainText("RSS_DELETE")
) -> None:
    group_id = None
    guild_channel_id = None

    if isinstance(event, GroupMessageEvent):
        group_id = event.group_id
    elif isinstance(event, GuildMessageEvent):
        guild_channel_id = f"{event.guild_id}@{event.channel_id}"

    rss = Rss.get_one_by_name(name=rss_name)

    if rss is None:
        await RSS_DELETE.finish("❌ 删除失败！不存在该订阅！")
    elif guild_channel_id:
        if rss.delete_guild_channel(guild_channel=guild_channel_id):
            if not any([rss.group_id, rss.user_id, rss.guild_channel_id]):
                rss.delete_rss()
                tr.delete_job(rss)
            else:
                await tr.add_job(rss)
            await RSS_DELETE.finish(f"👏 当前子频道取消订阅 {rss.name} 成功！")
        else:
            await RSS_DELETE.finish(f"❌ 当前子频道没有订阅： {rss.name} ！")
    elif group_id:
        if rss.delete_group(group=str(group_id)):
            if not any([rss.group_id, rss.user_id, rss.guild_channel_id]):
                rss.delete_rss()
                tr.delete_job(rss)
            else:
                await tr.add_job(rss)
            await RSS_DELETE.finish(f"👏 当前群组取消订阅 {rss.name} 成功！")
        else:
            await RSS_DELETE.finish(f"❌ 当前群组没有订阅： {rss.name} ！")
    else:
        rss.delete_rss()
        tr.delete_job(rss)
        await RSS_DELETE.finish(f"👏 订阅 {rss.name} 删除成功！")
