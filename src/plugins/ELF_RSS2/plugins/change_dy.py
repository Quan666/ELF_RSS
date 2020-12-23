from RSSHUB import rsstrigger as TR, RWlist,RSS_class
from nonebot import on_command, permission, require
from nonebot.adapters.cqhttp import Bot, Event
from nonebot.log import logger
from nonebot.rule import to_me

scheduler = require("nonebot_plugin_apscheduler").scheduler

# 存储目录
# file_path = './data/'

RssChange = on_command('change', aliases={'修改订阅', 'moddy'}, rule=to_me(), priority=5,
                       permission=permission.SUPERUSER|permission.GROUP_ADMIN)


@RssChange.handle()
async def handle_first_receive(bot: Bot, event: Event, state: dict):
    args = str(event.message).strip()
    if args:
        state["RssChange"] = args  # 如果用户发送了参数则直接赋值
    else:
        await RssChange.send('请输入要修改的订阅'\
        '\n订阅名 属性=,值'\
        '\n如:'\
        '\ntest qq=,123,234 qun=-1'\
        '\n对应参数:'\
        '\n订阅链接-url QQ-qq 群-qun 更新频率-time'\
        '\n代理-proxy 翻译-tl 仅title-ot，仅图片-op'\
        '\n注：'\
        '\nproxy、tl、ot、op 值为 1/0'\
        '\nQQ、群号前加英文逗号表示追加,-1设为空'\
        '\n各个属性空格分割'.strip())


@RssChange.got("RssChange",prompt='')
async def handle_RssAdd(bot: Bot, event: Event, state: dict):
    change_info = state["RssChange"]
    try:
        group_id = event.group_id
    except:
        group_id = None
    change_list = change_info.split(' ')
    try:
        name = change_list[0]
        change_list.remove(name)
    except:
        await RssChange.send('订阅名称参数错误！')
        return

    rss = RSS_class.rss(name,'','-1','-1')
    if not rss.findName(name=name):
        await RssChange.send('订阅 {} 不存在！'.format(name))
        return

    rss = rss.findName(name=name)
    if group_id:
        if not str(group_id) in rss.group_id:
            await RssChange.send('修改失败，当前群组无权操作订阅：{}'.format(rss.name))
            return
    try:
        for change_tmp in change_list:
            one_info_list = change_tmp.split('=', 1)
            if one_info_list[0]=='qq' and not group_id:# 暂时禁止群管理员修改 QQ
                if one_info_list[1]=='-1':
                    rss.user_id=[]
                    continue
                qq_list = one_info_list[1].split(',')
                # 表示追加
                if qq_list[0] == '':
                    qq_list.remove(qq_list[0])
                    for qq_tmp in qq_list:
                        if not qq_tmp in rss.user_id:
                            rss.user_id.append(str(qq_tmp))
                else:
                    rss.user_id=qq_list
            elif one_info_list[0]=='qun'and not group_id: # 暂时禁止群管理员修改群号，如要取消订阅可以使用 deldy 命令
                if one_info_list[1]=='-1':
                    rss.group_id=[]
                    continue
                qun_list = one_info_list[1].split(',')
                # 表示追加
                if qun_list[0] == '':
                    qun_list.remove(qun_list[0])
                    for qun_tmp in qun_list:
                        if not qun_tmp in rss.group_id:
                            rss.group_id.append(str(qun_tmp))
                else:
                    rss.group_id=qun_list
            elif one_info_list[0]=='url':
                rss.url = one_info_list[1]
            elif one_info_list[0]=='time':
                time = int(one_info_list[1])
                if time < 1:
                    rss.time = 1
                else:
                    rss.time = time
            elif one_info_list[0]=='proxy':
                rss.img_proxy = bool(int(one_info_list[1]))
            elif one_info_list[0]=='tl':
                rss.translation = bool(int(one_info_list[1]))
            elif one_info_list[0]=='ot':
                rss.only_title = bool(int(one_info_list[1]))
            elif one_info_list[0]=='op':
                rss.only_pic = bool(int(one_info_list[1]))
            else:
                await RssChange.send('参数错误或无权修改！\n{}'.format(change_tmp))
                return
        # 参数解析完毕，写入
        rss.writeRss()
        # 加入定时任务
        await TR.addJob(rss)
        if group_id:
            # 隐私考虑，群组下不展示除当前群组外的群号和QQ
            # 奇怪的逻辑，群管理能修改订阅消息，这对其他订阅者不公平。
            rss.group_id=[str(group_id),'*']
            rss.user_id=['*']
        await RssChange.send('修改成功\n{}'.format(rss.toString()))
        logger.info('修改成功\n{}'.format(rss.toString()))
    except BaseException as e:
        await RssChange.send('参数解析出现错误！\nE: {}'.format(str(e)))
        logger.error('参数解析出现错误！\nE: {}'.format(str(e)))
