import re

from RSSHUB import RSS_class, RWlist, rsstrigger as TR
from nonebot import on_command, permission
from nonebot.adapters.cqhttp import Bot, Event
from nonebot.log import logger
from nonebot.rule import to_me

from bot import config

RssAdd = on_command('add', aliases={'订阅', 'rssadd', 'dy'}, rule=to_me(), priority=5, permission=permission.SUPERUSER)


@RssAdd.handle()
async def handle_first_receive(bot: Bot, event: Event, state: dict):
    args = str(event.message).strip()  # 首次发送命令时跟随的参数，例：/天气 上海，则args为上海
    if args:
        state["RssAdd"] = args  # 如果用户发送了参数则直接赋值


@RssAdd.got("RssAdd",
            prompt="要订阅的信息不能为空呢，请重新输入\n输入样例：\ntest /twitter/user/xx 11,11 -1 5 0 1 \n订阅名 订阅地址 qq(,分隔，为空-1) 群号(,分隔，为空-1) 更新时间(分钟，可选) 1/0(代理，可选)")
async def handle_RssAdd(bot: Bot, event: Event, state: dict):
    rss_dy_link = state["RssAdd"]
    user_id = event.user_id
    try:
        group_id = event.group_id
    except:
        group_id = None

    # if group_id:
    #     rss_dy_link = await RssAdd.reject('要订阅的信息不能为空呢，请重新输入\n输入样例：\ntest /twitter/user/xx \n关于插件：http://ii1.fun/7byIVb')
    # else:
    #     rss_dy_link = await RssAdd.reject('要订阅的信息不能为空呢，请重新输入\n输入样例：\ntest /twitter/user/xx 11,11 -1 5 1 0 \n订阅名 订阅地址 qq(,分隔，为空-1) 群号(,分隔，为空-1) 更新时间(分钟，可选) 1/0(代理，可选) 1/0(翻译,可选) 1/0(仅标题,可选) 1/0(仅图片,可选)')

    # 获取、处理信息
    dy = rss_dy_link.split(' ')
    try:
        name = dy[0]
        name = re.sub(r'\?|\*|\:|\"|\<|\>|\\|/|\|', '_', name)
        if name == 'rss':
            name = 'rss_'
        try:
            url = dy[1]
        except:
            url = None
        flag = 0
        try:
            list_rss = RWlist.readRss()
            for old in list_rss:
                if old.name == name and not url:
                    old_rss = old
                    flag = 1
                elif str(old.url).lower() in str(url).lower():
                    old_rss = old
                    flag = 2
                elif old.name == name:
                    flag = 3
        except BaseException as e:
            logger.info("E :" + str(e))
        if group_id:
            if flag == 0 and url:
                if len(dy) > 2:
                    only_title = bool(int(dy[2]))
                else:
                    only_title = False
                if len(dy) > 3:
                    only_pic = bool(int(dy[3]))
                else:
                    only_pic = False
                translation = False
                times = int(config.add_uptime)
                proxy = config.add_proxy
                if user_id in config.SUPERUSERS and len(dy) > 4:
                    proxy = bool(int(dy[4]))
                if user_id in config.SUPERUSERS and len(dy) > 5:
                    times = int(dy[5])
                user_id = -1
            else:
                if flag == 1 or flag == 2:
                    if str(group_id) not in str(old_rss.group_id):
                        list_rss.remove(old_rss)
                        old_rss.group_id.append(str(group_id))
                        list_rss.append(old_rss)
                        RWlist.writeRss(list_rss)
                        if flag == 1:
                            await RssAdd.send(str(name) + '订阅名已存在，自动加入现有订阅，订阅地址为：' + str(old_rss.url))
                        else:
                            await RssAdd.send(str(url) + '订阅链接已存在，订阅名使用已有的订阅名"' + str(old_rss.name) + '"，订阅成功！')
                    else:
                        await RssAdd.send('订阅链接已经存在！')
                elif not url:
                    await RssAdd.send('订阅名不存在！')
                else:
                    await RssAdd.send('订阅名已存在，请更换个订阅名订阅')
                return
        elif user_id and flag == 0:
            user_id = dy[2]
            group_id = dy[3]
            if len(dy) > 4 and int(dy[4]) > 0:
                times = int(dy[4])
            else:
                times = 5
            if len(dy) > 5:
                proxy = bool(int(dy[5]))
            else:
                proxy = False
            if len(dy) > 6:
                notrsshub = bool(int(dy[6]))
            else:
                notrsshub = False
            if len(dy) > 7:
                translation = bool(int(dy[6]))
            else:
                translation = False
            if len(dy) > 8:
                only_title = bool(int(dy[7]))
            else:
                only_title = False
            if len(dy) > 9:
                only_pic = bool(int(dy[8]))
            else:
                only_pic = False
        else:
            # 向用户发送失败信息
            logger.info('添加' + name + '失败，已存在')
            await RssAdd.send('订阅名或订阅链接已经存在！')
            return
        rss = RSS_class.rss(name, url, str(user_id), str(group_id), times, proxy, notrsshub, translation, only_title,
                            only_pic)
        # 写入订阅配置文件
        try:
            list_rss.append(rss)
            RWlist.writeRss(list_rss)
        except:
            list_rss = []
            list_rss.append(rss)
            RWlist.writeRss(list_rss)
        if flag == 0:
            # 加入订阅任务队列
            TR.rss_trigger(times, rss)
            logger.info('添加' + rss.name + '成功')
            # 向用户发送成功信息
            await RssAdd.send(rss.name + '订阅成功！')
    except BaseException as e:
        logger.info(e)
        await RssAdd.send('参数不对哟！\n关于插件：http://ii1.fun/7byIVb')
