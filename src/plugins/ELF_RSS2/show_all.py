import re

from nonebot import on_command
from nonebot import permission as su
from nonebot.adapters.cqhttp import Bot, Event, GroupMessageEvent, permission, unescape
from nonebot.rule import to_me

from .RSS import rss_class
from .show_dy import handle_rss_list

RSS_SHOW_ALL = on_command(
    "show_all",
    aliases={"showall", "select_all", "selectall", "所有订阅"},
    rule=to_me(),
    priority=5,
    permission=su.SUPERUSER | permission.GROUP_ADMIN | permission.GROUP_OWNER,
)


@RSS_SHOW_ALL.handle()
async def handle_first_receive(bot: Bot, event: Event, state: dict):
    args = str(event.get_message()).strip()  # 首次发送命令时跟随的参数，例：/天气 上海，则args为上海
    if args:
        search_keyword = unescape(args)  # 如果用户发送了参数则直接赋值
    else:
        search_keyword = None

    group_id = None
    if isinstance(event, GroupMessageEvent):
        group_id = event.group_id

    rss = rss_class.Rss()
    if group_id:
        rss_list = rss.find_group(group=str(group_id))
        if not rss_list:
            await RSS_SHOW_ALL.send("❌ 当前群组没有任何订阅！")
            return
    else:
        rss_list = rss.read_rss()

    result = []
    if search_keyword:
        for i in rss_list:
            test = re.search(search_keyword, i.name, flags=re.I) or re.search(
                search_keyword, i.url, flags=re.I
            )
            if not group_id and search_keyword.isdigit():
                if i.user_id:
                    test = test or search_keyword in i.user_id
                if i.group_id:
                    test = test or search_keyword in i.group_id
            if test:
                result.append(i)
    else:
        result = rss_list

    if result:
        msg_str = await handle_rss_list(result)
        await RSS_SHOW_ALL.send(msg_str)
    else:
        await RSS_SHOW_ALL.send("❌ 当前没有任何订阅！")
