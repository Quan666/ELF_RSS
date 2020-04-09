from nonebot import on_command, CommandSession
import requests
from .RSSHub import rsshub
from .RSSHub import RSS_class
from .RSSHub import RWlist
from .RSSHub import rsstrigger as TR
import logging
from nonebot.log import logger
import config
import nonebot
from apscheduler.triggers.interval import IntervalTrigger # 间隔触发器
from nonebot import on_command, scheduler

# on_command 装饰器将函数声明为一个命令处理器
@on_command('change')
async def change(session: CommandSession):
    change_info = session.get('change',
                           prompt='输入要修改的订阅的 \n订阅名，修改项=,属性 \n如:\n 订阅 dyqq=,xx dsf=0\n对应参数： 订阅地址-url，订阅QQ-dyqq，订阅群-dyqun，更新频率-uptime，代理-proxy，第三方-dsf\n\n注：\n代理、第三方属性值为1/0\nqq、群号前加英文逗号表示追加')
    # 权限判断
    user_id = session.ctx['user_id']
    # print(type(user_id),type(config.ROOTUSER))
    if user_id == config.ROOTUSER:

        flag = 0

        try:
            list_rss = RWlist.readRss()
            # 获取、处理信息
            list_info = change_info.split(' ')
            name = list_info[0]  # 取订阅名
            list_info.pop(0)  # 从列表删除
            for rss_ in list_rss:
                if rss_.name == name :
                    rss_a=rss_
                    flag = flag + 1
            if flag <= 0:
                await session.send('订阅 ' + rss_name + ' 不存在！')
            else:
                try:
                    rss_tmp = rss_a
                    for info in list_info:
                        info_this = info.split('=')
                        if info_this[0] == 'url':
                            rss_tmp.url = info_this[1]
                        if info_this[0] == 'dyqq':
                            list_user_id = info_this[1].split(',')
                            if list_user_id[0] == '':
                                list_user_id.pop(0)
                                rss_tmp.user_id = rss_tmp.user_id + list_user_id
                            else:
                                if info_this[1]!='-1':
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
                            print(bool(info_this[1]))
                        if info_this[0] == 'dsf':
                            rss_tmp.notrsshub = bool(int(info_this[1]))
                    list_rss.remove(rss_a)
                    list_rss.append(rss_tmp)
                    RWlist.writeRss(list_rss)
                    try:
                        scheduler.remove_job(name)
                    except Exception as e:
                        print(e)
                    # 加入订阅任务队列
                    TR.rss_trigger(rss_tmp.time, rss_tmp)
                    logger.info('添加' + name + '成功')
                    await session.send('修改 ' + name + ' 订阅成功！')
                except Exception as e:
                    await session.send('修改失败！')
                    print(e)
        except:
            await session.send('你还没有任何订阅！')
    else:
        await session.send('你没有权限进行此操作！\n关于插件：http://ii1.fun/7byIVb')








# deldy.args_parser 装饰器将函数声明为 add 命令的参数解析器
# 命令解析器用于将用户输入的参数解析成命令真正需要的数据
@change.args_parser
async def _(session: CommandSession):
    # 去掉消息首尾的空白符
    stripped_arg = session.current_arg_text.strip()

    if session.is_first_run:
        # 该命令第一次运行（第一次进入命令会话）
        if stripped_arg:
            session.state['change'] = stripped_arg
        return

    if not stripped_arg:
        # 用户没有发送有效的订阅（而是发送了空白字符），则提示重新输入
        # 这里 session.pause() 将会发送消息并暂停当前会话（该行后面的代码不会被运行）
        session.pause(
            '输入不能为空！')

    # 如果当前正在向用户询问更多信息，且用户输入有效，则放入会话状态
    session.state[session.current_key] = stripped_arg
