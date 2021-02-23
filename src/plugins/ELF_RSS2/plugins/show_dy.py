from nonebot import on_command
from nonebot import permission as SUPERUSER
from nonebot.adapters.cqhttp import Bot, Event, permission, unescape
from nonebot.rule import to_me

from .RSSHUB import RSS_class

RssShow = on_command('show', aliases={'查看订阅'}, rule=to_me(
), priority=5, permission=SUPERUSER.SUPERUSER | permission.GROUP_ADMIN)

# 不带订阅名称默认展示当前群组或账号的订阅
# 带订阅名称就显示该订阅的


@RssShow.handle()
async def handle_first_receive(bot: Bot, event: Event, state: dict):
    args = str(event.message).strip()  # 首次发送命令时跟随的参数，例：/天气 上海，则args为上海
    if args:
        rss_name = unescape(args)  # 如果用户发送了参数则直接赋值
    else:
        rss_name = None
    user_id = event.user_id
    try:
        group_id = event.group_id
    except:
        group_id = None

    rss = RSS_class.rss('', '', '-1', '-1')

    if rss_name:
        rss = rss.findName(str(rss_name))
        if not rss:
            await RssShow.send('❌ 订阅 {} 不存在！'.format(rss_name))
            return
        if group_id:
            # 隐私考虑，群组下不展示除当前群组外的群号和QQ
            if not str(group_id) in rss.group_id:
                await RssShow.send('❌ 当前群组未订阅 {} '.format(rss_name))
                return
            rss.group_id = [str(group_id), '*']
            rss.user_id = ['*']
        await RssShow.send(rss.toString())
        return

    if group_id:
        rss_list = rss.findGroup(group=str(group_id))
        if not rss_list:
            await RssShow.send('❌ 当前群组没有任何订阅！')
            return
    else:
        rss_list = rss.findUser(user=str(user_id))
    if rss_list:
        if len(rss_list) == 1:
            await RssShow.send(rss_list[0].toString())
        else:
            flag = 0
            info = ''
            for rss_tmp in rss_list:
                if flag % 5 == 0 and flag != 0:
                    await RssShow.send(str(info))
                    info = ''
                info += 'Name：{}\nURL：{}\n\n'.format(rss_tmp.name, rss_tmp.url)
                flag += 1
            await RssShow.send(info+'共 {} 条订阅'.format(flag))

    else:
        await RssShow.send('❌ 当前没有任何订阅！')
        return

# @RssShow.got("RssShow", prompt="")
# async def handle_RssAdd(bot: Bot, event: Event, state: dict):
#     rss_name = state["RssShow"]
