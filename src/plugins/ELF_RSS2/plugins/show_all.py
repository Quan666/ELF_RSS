from RSSHUB import RWlist
from nonebot import on_command, permission
from nonebot.adapters.cqhttp import Bot, Event
from nonebot.rule import to_me

RssShowAll = on_command('showall', aliases={'showall', 'seeall'}, rule=to_me(), priority=5,
                        permission=permission.SUPERUSER)


@RssShowAll.handle()
async def handle_first_receive(bot: Bot, event: Event, state: dict):
    user_id = event.user_id
    try:
        group_id = event.group_id
    except:
        group_id = None
    flag = 0
    msg = ''
    try:
        list_rss = RWlist.readRss()
    except:
        await RssShowAll.send('获取rss列表失败')
        return
    if group_id:
        try:
            for rss_ in list_rss:
                if str(group_id) in str(rss_.group_id):
                    msg = msg + '名称：' + rss_.name + '\n订阅地址：' + rss_.url + '\n\n'
                    flag += 1
                    if (flag % 5 == 0):
                        await RssShowAll.send(msg)
                        msg = ''
            if flag <= 0:
                await RssShowAll.send('没有找到订阅哟！')
            else:
                await RssShowAll.send(msg + '共' + str(flag) + '条订阅')
        except:
            await RssShowAll.send('本群还没有任何订阅！')
    elif user_id:
        # 获取、处理信息
        try:
            for rss_ in list_rss:
                msg = msg + '名称：' + rss_.name + '\n订阅地址：' + rss_.url + '\n\n'
                flag += 1
                # 每条信息展示 5 条订阅
                if (flag % 5 == 0):
                    await RssShowAll.send(msg)
                    msg = ''
            if flag <= 0:
                await RssShowAll.send('没有找到订阅哟！')
            else:
                await RssShowAll.send(msg + '共' + str(flag) + '条订阅')
        except:
            await RssShowAll.send('还没有任何订阅！')
    else:
        await RssShowAll.send('你没有权限进行此操作！\n关于插件：http://ii1.fun/7byIVb')
