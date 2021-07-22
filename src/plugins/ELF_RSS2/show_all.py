import re

from nonebot import on_command
from nonebot import permission as su
from nonebot.adapters.cqhttp import Bot, Event, GroupMessageEvent, permission, unescape
from nonebot.rule import to_me

from .RSS import rss_class
from .show_dy import handle_rss_list

RSS_SHOW_ALL = on_command(
    "showall",
    aliases={"selectall", "所有订阅"},
    rule=to_me(),
    priority=5,
    permission=su.SUPERUSER | permission.GROUP_ADMIN | permission.GROUP_OWNER,
)


@RSS_SHOW_ALL.handle()
async def handle_first_receive(bot: Bot, event: Event, state: dict):
    args = str(event.get_message()).strip()  # 首次发送命令时跟随的参数，例：/天气 上海，则args为上海
    if args:
        rss_name_search = unescape(args)  # 如果用户发送了参数则直接赋值
    else:
        rss_name_search = None

    group_id = None
    if isinstance(event, GroupMessageEvent):
        group_id = event.group_id

    rss = rss_class.Rss("", "", "-1", "-1")
    if group_id:
        rss_list = rss.find_group(group=str(group_id))
        if not rss_list:
            await RSS_SHOW_ALL.send("❌ 当前群组没有任何订阅！")
            return
    else:
        rss_list = rss.read_rss()

    if rss_name_search:
        rss_list = [
            i for i in rss_list if re.search(rss_name_search, f"{i.name}|{i.url}")
        ]

    if rss_list:
        msg_str = await handle_rss_list(rss_list)
        await RSS_SHOW_ALL.send(msg_str)
    else:
        await RSS_SHOW_ALL.send("❌ 当前没有任何订阅！")
