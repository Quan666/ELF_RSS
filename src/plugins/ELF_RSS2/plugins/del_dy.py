import os
import re
from pathlib import Path

from RSSHUB import RWlist
from nonebot import on_command, require, permission
from nonebot.adapters.cqhttp import Bot, Event
from nonebot.log import logger
from nonebot.rule import to_me

scheduler = require("nonebot_plugin_apscheduler").scheduler
# 存储目录
file_path = Path.cwd() / 'data'

Rssdel = on_command('deldy', aliases={'delrss', 'rssdel'}, rule=to_me(), priority=5, permission=permission.SUPERUSER)


@Rssdel.handle()
async def handle_first_receive(bot: Bot, event: Event, state: dict):
    args = str(event.message).strip()  # 首次发送命令时跟随的参数，例：/天气 上海，则args为上海
    if args:
        state["Rssdel"] = args  # 如果用户发送了参数则直接赋值


@Rssdel.got("Rssdel", prompt="输入要删除的订阅名或订阅地址")
async def handle_RssAdd(bot: Bot, event: Event, state: dict):
    rss_name = state["Rssdel"]
    user_id = event.user_id
    try:
        group_id = event.group_id
    except:
        group_id = None

    # 获取、处理信息
    flag = 0
    try:
        list_rss = RWlist.readRss()
        if group_id:
            for rss_ in list_rss:
                if (rss_.name == rss_name and str(group_id) in str(rss_.group_id)) or (
                        rss_.url == rss_name and str(group_id) in str(rss_.group_id)):
                    rss_tmp = rss_
                    if rss_tmp.group_id[0] == str(group_id):
                        rss_tmp.group_id.pop(0)
                    else:
                        rss_tmp.group_id = eval(re.sub(f", '{group_id}'", "", str(rss_tmp.group_id)))
                    await Rssdel.send('本群订阅 ' + rss_name + ' 删除成功！')
                    if not rss_tmp.group_id and not rss_tmp.user_id:
                        list_rss.remove(rss_)
                        scheduler.remove_job(rss_.name)
                        try:
                            os.remove(file_path / (rss_.name + ".json"))
                        except BaseException as e:
                            logger.info(e)
                        RWlist.writeRss(list_rss)
                    else:
                        list_rss.remove(rss_)
                        list_rss.append(rss_tmp)
                        RWlist.writeRss(list_rss)
        elif user_id:
            for rss_ in list_rss:
                if rss_.name == rss_name or rss_.url == rss_name:
                    list_rss.remove(rss_)
                    scheduler.remove_job(rss_.name)
                    try:
                        os.remove(file_path / (rss_.name + ".json"))
                    except BaseException as e:
                        logger.info(e)
                    await Rssdel.send('订阅 ' + rss_name + ' 删除成功！')
                    flag = flag + 1
            if flag <= 0:
                await Rssdel.send('订阅 ' + rss_name + ' 删除失败！该订阅不存在！')
            else:
                RWlist.writeRss(list_rss)
                await Rssdel.send('删除 ' + str(flag) + ' 条订阅！')
    except BaseException as e:
        # logger.info(e)
        await Rssdel.send('你还没有任何订阅！\n关于插件：http://ii1.fun/7byIVb')
