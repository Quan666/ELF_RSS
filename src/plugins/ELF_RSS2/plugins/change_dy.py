from RSSHUB import rsstrigger as TR, RWlist
# from nonebot import scheduler,
from nonebot import on_command, permission, require
from nonebot.adapters.cqhttp import Bot, Event
from nonebot.log import logger
from nonebot.rule import to_me

scheduler = require("nonebot_plugin_apscheduler").scheduler
# from pathlib impo
# 存储目录
# file_path = './data/'

RssChange = on_command('change', aliases={'changedy', 'moddy'}, rule=to_me(), priority=5,
                       permission=permission.SUPERUSER)


@RssChange.handle()
async def handle_first_receive(bot: Bot, event: Event, state: dict):
    args = str(event.message).strip()  # 首次发送命令时跟随的参数，例：/天气 上海，则args为上海
    if args:
        state["RssChange"] = args  # 如果用户发送了参数则直接赋值


@RssChange.got("RssChange",
               prompt='输入要修改的订阅的 \n订阅名 修改项=,属性 \n如:\n 订阅 dyqq=,xx dsf=0\n对应参数:地址-url，QQ-dyqq，群-dyqun，更新频率-uptime，代理-proxy,翻译-tl，仅title-ot，仅图片-op\n注：\n代理、翻译、仅title属性值为1/0\nqq、群号前加英文逗号表示追加')
async def handle_RssAdd(bot: Bot, event: Event, state: dict):
    change_info = state["RssChange"]
    # user_id = event.user_id
    # try:
    #     group_id = event.group_id
    # except:
    #     group_id = None

    flag = 0
    try:
        list_rss = RWlist.readRss()
        # 获取、处理信息
        list_info = change_info.split(' ')
        name = list_info[0]  # 取订阅名
        list_info.pop(0)  # 从列表删除
        for rss_ in list_rss:
            if rss_.name == name:
                rss_a = rss_
                flag = flag + 1
        if flag <= 0:
            await RssChange.send('订阅 ' + name + ' 不存在！')
        else:
            try:
                rss_tmp = rss_a
                for info in list_info:
                    info_this = info.split('=', 1)
                    if info_this[0] == 'url':
                        rss_tmp.url = info_this[1]
                    if info_this[0] == 'dyqq':
                        list_user_id = info_this[1].split(',')
                        if list_user_id[0] == '':
                            list_user_id.pop(0)
                            rss_tmp.user_id = rss_tmp.user_id + list_user_id
                        else:
                            if info_this[1] != '-1':
                                rss_tmp.user_id = list_user_id
                            else:
                                rss_tmp.user_id = []
                    if info_this[0] == 'dyqun':
                        list_group_id = info_this[1].split(',')
                        if list_group_id[0] == '':
                            list_group_id.pop(0)
                            rss_tmp.group_id = rss_tmp.group_id + list_group_id
                        else:
                            if info_this[1] != '-1':
                                rss_tmp.group_id = list_group_id
                            else:
                                rss_tmp.group_id = []
                    if info_this[0] == 'uptime':
                        rss_tmp.time = int(info_this[1])
                    if info_this[0] == 'proxy':
                        rss_tmp.img_proxy = bool(int(info_this[1]))
                    if info_this[0] == 'dsf':
                        rss_tmp.notrsshub = bool(int(info_this[1]))
                    if info_this[0] == 'tl':
                        rss_tmp.translation = bool(int(info_this[1]))
                    if info_this[0] == 'ot':
                        rss_tmp.only_title = bool(int(info_this[1]))
                    if info_this[0] == 'op':
                        rss_tmp.only_pic = bool(int(info_this[1]))
                list_rss.remove(rss_a)
                list_rss.append(rss_tmp)
                RWlist.writeRss(list_rss)
                try:
                    scheduler.remove_job(name)
                except Exception as e:
                    logger.error(e)
                # 加入订阅任务队列
                TR.rss_trigger(rss_tmp.time, rss_tmp)
                logger.info('修改' + name + '成功')
                await RssChange.send('修改 ' + name + ' 订阅成功！')
            except Exception as e:
                await RssChange.send('命令出错，修改失败！')
                logger.error(e)
    except:
        await RssChange.send('你还没有任何订阅！\n关于插件：http://ii1.fun/7byIVb')
