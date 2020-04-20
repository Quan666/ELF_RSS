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
@on_command('show')
async def show(session: CommandSession):
    rss_name = session.get('show', prompt='输入要查看的订阅名或订阅地址')
    # 权限判断
    user_id = session.ctx['user_id']
    # print(type(user_id),type(config.ROOTUSER))
    if int(user_id) in config.ROOTUSER:
        # 获取、处理信息

        flag = 0

        try:
            list_rss = RWlist.readRss()
            for rss_ in list_rss:
                if rss_.name == rss_name or rss_.url == rss_name:
                    await session.send(
                        '名称：' + rss_.name + '\n订阅地址：' + rss_.url + '\n订阅QQ：' + str(rss_.user_id) + '\n订阅群：' + str(
                            rss_.group_id) + '\n更新频率：' + str(rss_.time) + '分钟/次\n代理：' + str(rss_.img_proxy) + '\n第三方：' + str(rss_.notrsshub))
                    flag = flag + 1
            if flag <= 0:
                await session.send('没有找到 ' + rss_name + ' 的订阅哟！')
        except:
            await session.send('你还没有任何订阅！')
    else:
        await session.send('你没有权限进行此操作！\n关于插件：http://ii1.fun/7byIVb')


# show.args_parser 装饰器将函数声明为 add 命令的参数解析器
# 命令解析器用于将用户输入的参数解析成命令真正需要的数据
@show.args_parser
async def _(session: CommandSession):
    # 去掉消息首尾的空白符
    stripped_arg = session.current_arg_text.strip()

    if session.is_first_run:
        # 该命令第一次运行（第一次进入命令会话）
        if stripped_arg:
            session.state['show'] = stripped_arg
        return

    if not stripped_arg:
        # 用户没有发送有效的订阅（而是发送了空白字符），则提示重新输入
        # 这里 session.pause() 将会发送消息并暂停当前会话（该行后面的代码不会被运行）
        session.pause(
            '输入不能为空！')

    # 如果当前正在向用户询问更多信息，且用户输入有效，则放入会话状态
    session.state[session.current_key] = stripped_arg
