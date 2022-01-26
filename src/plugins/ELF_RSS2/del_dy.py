from nonebot import on_command
from nonebot.adapters.onebot.v11 import Event, GroupMessageEvent, Message, unescape
from nonebot.adapters.onebot.v11.permission import GROUP_ADMIN, GROUP_OWNER
from nonebot.params import CommandArg, State
from nonebot.permission import SUPERUSER
from nonebot.rule import to_me
from nonebot.typing import T_State

from .RSS import my_trigger as tr
from .RSS import rss_class

RSS_DELETE = on_command(
    "deldy",
    aliases={"drop", "删除订阅"},
    rule=to_me(),
    priority=5,
    permission=GROUP_ADMIN | GROUP_OWNER | SUPERUSER,
)


@RSS_DELETE.handle()
async def handle_first_receive(
    message: Message = CommandArg(), state: T_State = State()
):
    args = str(message).strip()
    if args:
        state["RSS_DELETE"] = unescape(args)


@RSS_DELETE.got("RSS_DELETE", prompt="输入要删除的订阅名")
async def handle_rss_delete(event: Event, state: T_State = State()):
    rss_name = unescape(str(state["RSS_DELETE"]))

    group_id = None

    if isinstance(event, GroupMessageEvent):
        group_id = event.group_id

    rss = rss_class.Rss()
    if rss.find_name(name=rss_name):
        rss = rss.find_name(name=rss_name)
    else:
        await RSS_DELETE.finish("❌ 删除失败！不存在该订阅！")

    if group_id:
        if rss.delete_group(group=group_id):
            if not rss.group_id and not rss.user_id:
                rss.delete_rss()
                await tr.delete_job(rss)
            else:
                await tr.add_job(rss)
            await RSS_DELETE.finish(f"👏 当前群组取消订阅 {rss.name} 成功！")
        else:
            await RSS_DELETE.finish(f"❌ 当前群组没有订阅： {rss.name} ！")
    else:
        rss.delete_rss()
        await tr.delete_job(rss)
        await RSS_DELETE.finish(f"👏 订阅 {rss.name} 删除成功！")
