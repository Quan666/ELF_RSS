from nonebot import on_command
from nonebot import permission as SUPERUSER
from nonebot.adapters.cqhttp import Bot, Event, permission
from nonebot.rule import to_me

from .RSSHUB import RSS_class

RssShowAll = on_command('showall', aliases={'selectall', '所有订阅'}, rule=to_me(), priority=5,
                        permission=SUPERUSER.SUPERUSER | permission.GROUP_ADMIN)


@RssShowAll.handle()
async def handle_first_receive(bot: Bot, event: Event, state: dict):
    user_id = event.user_id
    try:
        group_id = event.group_id
    except:
        group_id = None

    rss = RSS_class.rss('', '', '-1', '-1')
    if group_id:
        rss_list = rss.findGroup(group=str(group_id))
        if not rss_list:
            await RssShowAll.send('当前群组没有任何订阅！')
            return
    else:
        rss_list = rss.readRss()
    if rss_list:
        if len(rss_list) == 1:
            await RssShowAll.send(rss_list[0].toString())
        else:
            flag = 0
            info = ''
            for rss_tmp in rss_list:
                if flag % 5 == 0 and flag != 0:
                    await RssShowAll.send(str(info))
                    info = ''
                info += 'Name：{}\nURL：{}\n\n'.format(rss_tmp.name, rss_tmp.url)
                flag += 1
            await RssShowAll.send(info+'共 {} 条订阅'.format(flag))

    else:
        await RssShowAll.send('当前没有任何订阅！')
        return
