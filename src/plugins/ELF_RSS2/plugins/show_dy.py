import os
from pathlib import Path

from RSSHUB import RWlist
from nonebot import on_command
from nonebot import permission
from nonebot.adapters.cqhttp import Bot, Event
from nonebot.rule import to_me

# 存储目录
# file_path = str(str(Path.cwd()) + os.sep+'data' + os.sep)

RssShow = on_command('show', aliases={'showdy', 'lookdy'}, rule=to_me(), priority=5, permission=permission.SUPERUSER)


@RssShow.handle()
async def handle_first_receive(bot: Bot, event: Event, state: dict):
    args = str(event.message).strip()  # 首次发送命令时跟随的参数，例：/天气 上海，则args为上海
    if args:
        state["RssShow"] = args  # 如果用户发送了参数则直接赋值


@RssShow.got("RssShow", prompt="输入要查询的订阅名或订阅地址")
async def handle_RssAdd(bot: Bot, event: Event, state: dict):
    rss_name = state["RssShow"]
    # user_id = event.user_id
    # try:
    #     group_id = event.group_id
    # except:
    #     group_id = None

    flag = 0
    try:
        list_rss = RWlist.readRss()
        for rss_ in list_rss:
            if rss_.name == rss_name or rss_.url == rss_name:
                await RssShow.send(
                    '名称：' + rss_.name + '\n订阅地址：' + rss_.url + '\n订阅QQ：' + str(rss_.user_id) + '\n订阅群：' + str(
                        rss_.group_id) + '\n更新频率：' + str(rss_.time) + '分钟/次\n代理：' + str(
                        rss_.img_proxy) + '\n第三方：' + str(rss_.notrsshub)
                    + '\n翻译：' + str(rss_.translation) + '\n仅标题：' + str(rss_.only_title) + '\n仅图片：' + str(rss_.only_pic))
                flag = flag + 1
        if flag <= 0:
            await RssShow.send('没有找到 ' + rss_name + ' 的订阅哟！')
    except:
        await RssShow.send('你还没有任何订阅！\n关于插件：http://ii1.fun/7byIVb')
