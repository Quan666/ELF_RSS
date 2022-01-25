import re

from nonebot import on_command
from nonebot.adapters.onebot.v11 import Event, GroupMessageEvent, Message, unescape
from nonebot.adapters.onebot.v11.permission import GROUP_ADMIN, GROUP_OWNER
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER
from nonebot.rule import to_me

from .RSS import rss_class
from .show_dy import handle_rss_list

RSS_SHOW_ALL = on_command(
    "show_all",
    aliases={"showall", "select_all", "selectall", "所有订阅"},
    rule=to_me(),
    priority=5,
    permission=GROUP_ADMIN | GROUP_OWNER | SUPERUSER,
)


@RSS_SHOW_ALL.handle()
async def handle_first_receive(event: Event, message: Message = CommandArg()):
    args = str(message).strip()
    if args:
        search_keyword = unescape(args)
    else:
        search_keyword = None

    group_id = None

    if isinstance(event, GroupMessageEvent):
        group_id = event.group_id

    rss = rss_class.Rss()
    if group_id:
        rss_list = rss.find_group(group=str(group_id))
        if not rss_list:
            await RSS_SHOW_ALL.finish("❌ 当前群组没有任何订阅！")
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
        await RSS_SHOW_ALL.finish(msg_str)
    else:
        await RSS_SHOW_ALL.finish("❌ 当前没有任何订阅！")
