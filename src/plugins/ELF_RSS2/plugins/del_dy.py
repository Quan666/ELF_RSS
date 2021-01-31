import os
import re
from pathlib import Path
from RSSHUB import RSS_class, rsstrigger as TR
from RSSHUB import RWlist
from nonebot import on_command, require
from nonebot.adapters.cqhttp import permission, unescape
from nonebot import permission as SUPERUSER
from nonebot.adapters.cqhttp import Bot, Event
from nonebot.log import logger
from nonebot.rule import to_me

scheduler = require("nonebot_plugin_apscheduler").scheduler
# 存储目录
file_path = str(str(Path.cwd()) + os.sep+'data' + os.sep)

Rssdel = on_command('deldy', aliases={'drop', '删除订阅'}, rule=to_me(), priority=5, permission=SUPERUSER.SUPERUSER|permission.GROUP_ADMIN)


@Rssdel.handle()
async def handle_first_receive(bot: Bot, event: Event, state: dict):
    args = str(event.message).strip()  # 首次发送命令时跟随的参数，例：/天气 上海，则args为上海
    if args:
        state["Rssdel"] = unescape(args)  # 如果用户发送了参数则直接赋值


@Rssdel.got("Rssdel", prompt="输入要删除的订阅名")
async def handle_RssAdd(bot: Bot, event: Event, state: dict):
    rss_name = state["Rssdel"]
    try:
        group_id = event.group_id
    except:
        group_id = None

    rss = RSS_class.rss('','','-1','-1')
    if rss.findName(name=rss_name):
        rss = rss.findName(name=rss_name)
    else:
        await Rssdel.send('删除失败！不存在该订阅！')
        return

    if group_id:
        if rss.delGroup(group=group_id):
            await TR.addJob(rss)
            await Rssdel.send('当前群组取消订阅 {} 成功！'.format(rss.name))
        else:
            await Rssdel.send('当前群组没有订阅： {} ！'.format(rss.name))
    else:
        rss.delRss(rss)
        await TR.delJob(rss)
        await Rssdel.send('订阅 {} 删除成功！'.format(rss.name))