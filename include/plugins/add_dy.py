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


# on_command 装饰器将函数声明为一个命令处理器
# 这里 uri 为命令的名字，同时允许使用别名
@on_command('add', aliases=('订阅', 'dy', 'DY'))
async def add(session: CommandSession):
    # 从会话状态（session.state）中获取订阅信息链接(link)，如果当前不存在，则询问用户
    rss_dy_link = session.get('add', prompt='要订阅的信息不能为空呢，请重新输入\n输入样例：\ntest /twitter/user/xx 11,11 -1 5 1 0 \n订阅名 订阅地址 qq(,分隔，为空-1) 群号(,分隔，为空-1) 更新时间(分钟，可选) 1/0(代理，可选) 1/0(第三方订阅链接，可选) ')
    # 权限判断
    # 获取、处理信息
    dy = rss_dy_link.split(' ')
    # await session.send('')#反馈
    # print('\n\n\n'+str(len(dy)),dy[0]+'\n\n\n')
    name = dy[0]
    url = dy[1]
    user_id = dy[2]
    group_id = dy[3]
    if len(dy) > 4:
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
    rss = RSS_class.rss(name, url, user_id, group_id, times, proxy, notrsshub)
    # 写入订阅配置文件 # 先读看是否重复再写
    flag = 0
    bot = nonebot.get_bot()
    try:
        list_rss = RWlist.readRss()
        for old in list_rss:
            if old.name == rss.name or old.url == rss.url:
                flag = 1
        if flag == 0:
            list_rss.append(rss)
            RWlist.writeRss(list_rss)
        else:
            # 向用户发送失败信息
            logger.info('添加' + rss.name + '失败，已存在')
            await bot.send_msg(message_type='private', user_id=config.ROOTUSER, message='订阅名或订阅链接已经存在！')

    except:
        list_rss = []
        list_rss.append(rss)
        RWlist.writeRss(list_rss)
    if flag == 0:
        # 加入订阅任务队列
        TR.rss_trigger(times, rss)
        logger.info('添加' + rss.name + '成功')
        # 向用户发送成功信息
        await bot.send_msg(message_type='private', user_id=config.ROOTUSER, message=rss.name + '订阅成功！')


# add.args_parser 装饰器将函数声明为 add 命令的参数解析器
# 命令解析器用于将用户输入的参数解析成命令真正需要的数据
@add.args_parser
async def _(session: CommandSession):
    # 去掉消息首尾的空白符
    stripped_arg = session.current_arg_text.strip()

    if session.is_first_run:
        # 该命令第一次运行（第一次进入命令会话）
        if stripped_arg:
            # 第一次运行参数不为空，意味着用户直接将订阅信息跟在命令名后面，作为参数传入
            # 例如用户可能发送了：订阅 test1 /twitter/user/key_official 1447027111 1037939056 1 true true #订阅名 订阅地址 qq 群组 更新时间 代理 第三方
            session.state['add'] = stripped_arg
        return

    if not stripped_arg:
        # 用户没有发送有效的订阅（而是发送了空白字符），则提示重新输入
        # 这里 session.pause() 将会发送消息并暂停当前会话（该行后面的代码不会被运行）
        session.pause(
            '要订阅的信息不能为空呢，请重新输入\n输入样例：\ntest /twitter/user/xx 11,11 -1 5 True False \n订阅名 订阅地址 qq(,分隔，为空-1) 群号(,分隔，为空-1) 更新时间(分钟，可选) True/False(代理，可选) True/False(第三方订阅链接，可选) ')

    # 如果当前正在向用户询问更多信息（例如本例中的要压缩的链接），且用户输入有效，则放入会话状态
    session.state[session.current_key] = stripped_arg
