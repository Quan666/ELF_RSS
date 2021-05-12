from nonebot import on_command
from nonebot import permission as su
from nonebot.adapters.cqhttp import Bot, Event, GroupMessageEvent, permission, unescape
from nonebot.rule import to_me

from .RSS import rss_class

RSS_SHOW = on_command(
    "show",
    aliases={"查看订阅"},
    rule=to_me(),
    priority=5,
    permission=su.SUPERUSER | permission.GROUP_ADMIN | permission.GROUP_OWNER,
)


# 不带订阅名称默认展示当前群组或账号的订阅，带订阅名称就显示该订阅的
@RSS_SHOW.handle()
async def handle_first_receive(bot: Bot, event: Event, state: dict):
    args = str(event.get_message()).strip()  # 首次发送命令时跟随的参数，例：/天气 上海，则args为上海
    if args:
        rss_name = unescape(args)  # 如果用户发送了参数则直接赋值
    else:
        rss_name = None
    user_id = event.get_user_id()
    group_id = None
    if isinstance(event, GroupMessageEvent):
        group_id = event.group_id

    rss = rss_class.Rss("", "", "-1", "-1")

    if rss_name:
        rss = rss.find_name(str(rss_name))
        if not rss:
            await RSS_SHOW.send(f"❌ 订阅 {rss_name} 不存在！")
            return
        if group_id:
            # 隐私考虑，群组下不展示除当前群组外的群号和QQ
            if not str(group_id) in rss.group_id:
                await RSS_SHOW.send(f"❌ 当前群组未订阅 {rss_name} ")
                return
            rss.group_id = [str(group_id), "*"]
            rss.user_id = ["*"]
        await RSS_SHOW.send(str(rss))
        return

    if group_id:
        rss_list = rss.find_group(group=str(group_id))
        if not rss_list:
            await RSS_SHOW.send("❌ 当前群组没有任何订阅！")
            return
    else:
        rss_list = rss.find_user(user=str(user_id))
    if rss_list:
        if len(rss_list) == 1:
            await RSS_SHOW.send(str(rss_list[0]))
        else:
            flag = 0
            info = ""
            for rss_tmp in rss_list:
                if flag % 5 == 0 and flag != 0:
                    await RSS_SHOW.send(str(info))
                    info = ""
                info += f"Name：{rss_tmp.name}\nURL：{rss_tmp.url}\n\n"
                flag += 1
            await RSS_SHOW.send(f"{info}共 {flag} 条订阅")

    else:
        await RSS_SHOW.send("❌ 当前没有任何订阅！")
