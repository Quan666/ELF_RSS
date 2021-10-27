from nonebot import on_command
from nonebot import permission as su
from nonebot import require
from nonebot.adapters.cqhttp import Bot, Event, GroupMessageEvent, permission, unescape
from nonebot.rule import to_me

from .RSS import my_trigger as tr
from .RSS import rss_class

SCHEDULER = require("nonebot_plugin_apscheduler").scheduler

RSS_DELETE = on_command(
    "deldy",
    aliases={"drop", "删除订阅"},
    rule=to_me(),
    priority=5,
    permission=su.SUPERUSER | permission.GROUP_ADMIN | permission.GROUP_OWNER,
)


@RSS_DELETE.handle()
async def handle_first_receive(bot: Bot, event: Event, state: dict):
    args = str(event.get_message()).strip()  # 首次发送命令时跟随的参数，例：/天气 上海，则args为上海
    if args:
        state["RSS_DELETE"] = unescape(args)  # 如果用户发送了参数则直接赋值


@RSS_DELETE.got("RSS_DELETE", prompt="输入要删除的订阅名")
async def handle_rss_delete(bot: Bot, event: Event, state: dict):
    rss_name = unescape(state["RSS_DELETE"])
    group_id = None
    if isinstance(event, GroupMessageEvent):
        group_id = event.group_id

    rss = rss_class.Rss()
    if rss.find_name(name=rss_name):
        rss = rss.find_name(name=rss_name)
    else:
        await RSS_DELETE.send("❌ 删除失败！不存在该订阅！")
        return

    if group_id:
        if rss.delete_group(group=group_id):
            if not rss.group_id and not rss.user_id:
                rss.delete_rss()
                await tr.delete_job(rss)
            else:
                await tr.add_job(rss)
            await RSS_DELETE.send(f"👏 当前群组取消订阅 {rss.name} 成功！")
        else:
            await RSS_DELETE.send(f"❌ 当前群组没有订阅： {rss.name} ！")
    else:
        rss.delete_rss()
        await tr.delete_job(rss)
        await RSS_DELETE.send(f"👏 订阅 {rss.name} 删除成功！")
