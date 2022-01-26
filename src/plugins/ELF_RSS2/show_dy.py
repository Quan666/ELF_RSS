import copy

from nonebot import on_command
from nonebot.adapters.onebot.v11 import Event, GroupMessageEvent, Message, unescape
from nonebot.adapters.onebot.v11.permission import GROUP_ADMIN, GROUP_OWNER
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER
from nonebot.rule import to_me

from .RSS import rss_class

RSS_SHOW = on_command(
    "show",
    aliases={"查看订阅"},
    rule=to_me(),
    priority=5,
    permission=GROUP_ADMIN | GROUP_OWNER | SUPERUSER,
)


async def handle_rss_list(rss_list: list) -> str:
    rss_info_list = [f"{i.name}：{i.url}" for i in rss_list]
    rss_info_list.sort()
    msg_str = f"当前共有 {len(rss_info_list)} 条订阅：\n\n" + "\n\n".join(rss_info_list)
    rss_stopped_info_list = [f"{i.name}：{i.url}" for i in rss_list if i.stop]
    if rss_stopped_info_list:
        rss_stopped_info_list.sort()
        msg_str += (
            f"\n----------------------\n"
            f"其中共有 {len(rss_stopped_info_list)} 条订阅已停止更新：\n\n"
            + "\n\n".join(rss_stopped_info_list)
        )
    return msg_str


# 不带订阅名称默认展示当前群组或账号的订阅，带订阅名称就显示该订阅的
@RSS_SHOW.handle()
async def handle_first_receive(event: Event, message: Message = CommandArg()):
    args = str(message).strip()
    if args:
        rss_name = unescape(args)
    else:
        rss_name = None

    user_id = event.get_user_id()
    group_id = None

    if isinstance(event, GroupMessageEvent):
        group_id = event.group_id

    rss = rss_class.Rss()
    if rss_name:
        rss = rss.find_name(rss_name)
        if not rss:
            await RSS_SHOW.finish(f"❌ 订阅 {rss_name} 不存在！")
        rss_msg = str(rss)
        if group_id:
            # 隐私考虑，不展示除当前群组外的
            if not str(group_id) in rss.group_id:
                await RSS_SHOW.finish(f"❌ 当前群组未订阅 {rss_name} ")
            rss_tmp = copy.deepcopy(rss)
            rss_tmp.group_id = [str(group_id), "*"]
            rss_tmp.user_id = ["*"]
            rss_msg = str(rss_tmp)
        await RSS_SHOW.finish(rss_msg)

    if group_id:
        rss_list = rss.find_group(group=str(group_id))
        if not rss_list:
            await RSS_SHOW.finish("❌ 当前群组没有任何订阅！")
    else:
        rss_list = rss.find_user(user=user_id)

    if rss_list:
        msg_str = await handle_rss_list(rss_list)
        await RSS_SHOW.finish(msg_str)
    else:
        await RSS_SHOW.finish("❌ 当前没有任何订阅！")
