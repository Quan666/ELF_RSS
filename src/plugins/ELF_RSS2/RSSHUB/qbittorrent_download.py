import os
import re

import nonebot
from apscheduler.triggers.interval import IntervalTrigger
from nonebot import logger, require
from qbittorrent import Client
from starlette.responses import FileResponse
from ..config import config

# 计划
# 创建一个全局定时器用来检测种子下载情况
# 群文件上传成功回调
# 文件三种状态1.下载中2。上传中3.上传完成
# 文件信息持久化存储
# 关键词正则表达式
# 下载开关pip install cx_Freeze


app = nonebot.get_asgi()


@app.get("/elfrss/file/{filename}")
async def file(filename: str) -> FileResponse:
    path = (await get_qb()).get_default_save_path()
    return FileResponse(path=path + os.sep + filename, filename=filename)


async def send_Msg(msg: str):
    logger.info(msg)
    bot, = nonebot.get_bots().values()
    for group_id in config.down_status_msg_group:
        await bot.send_msg(message_type='group', group_id=int(group_id), message=msg)


async def get_qb():
    try:
        qb = Client(config.qb_web_url)
        qb.login()
    except BaseException as e:
        bot, = nonebot.get_bots().values()
        msg = '❌ 无法连接到 qbittorrent ,请检查：\n1.是否启动程序\n2.是否勾选了“Web用户界面（远程控制）”\n3.连接地址、端口是否正确\nE: {}'.format(e)
        logger.error(msg)
        await bot.send_msg(message_type='private', user_id=str(list(config.superusers)[0]), message=msg)
        return None
    try:
        qb.get_default_save_path()
    except BaseException as e:
        bot, = nonebot.get_bots().values()
        msg = '❌ 无法连登录到 qbittorrent ,请检查是否勾选 “对本地主机上的客户端跳过身份验证”。\nE: {}'.format(
            e)
        logger.error(msg)
        await bot.send_msg(message_type='private', user_id=str(list(config.superusers)[0]), message=msg)
        return None
    return qb


# 种子地址，种子下载路径，群文件上传 群列表，订阅名称
async def start_down(url: str, path: str, group_ids: list, name: str):
    qb = await get_qb()
    if not qb:
        return
    qb.download_from_link(link=url, path=path)
    res = re.search('[a-f0-9]{40}', url)
    hash = res[0]
    await rss_trigger(hash=hash, group_ids=group_ids, name=name)


async def check_down_status(hash: str, group_ids: list, name: str):
    qb = await get_qb()
    if not qb:
        return
    info = qb.get_torrent(hash)
    files = qb.get_torrent_files(hash)
    bot, = nonebot.get_bots().values()
    print(info['total_downloaded'] - info['total_size'])
    print(info['total_downloaded'], info['total_size'])
    if info['total_downloaded'] - info['total_size'] >= 0.000000:
        await send_Msg(str('👏 {}\nHash: {} \n下载完成！'.format(name, hash)))
        for group_id in group_ids:
            for tmp in files:
                # 异常包起来防止超时报错导致后续不执行
                try:
                    if config.local_ip and len(config.local_ip) >= 7:
                        # 通过这个API下载的文件能直接放入CQ码作为图片或语音发送 调用后会阻塞直到下载完成后才会返回数据，请注意下载大文件时的超时
                        await send_Msg('go-cqhttp 开始下载文件：{}'.format(tmp['name']))
                        path = (await bot.call_api('download_file',
                                                   url='http://{}:8080/elfrss/file/{}'.format(config.local_ip,
                                                                                              tmp['name']))).file
                    else:
                        path = info['save_path'] + tmp['name']
                    await send_Msg(str('{}\nHash: {} \n开始上传到群：{}'.format(name, hash, group_id)))
                    await bot.call_api('upload_group_file', group_id=group_id, file=path, name=tmp['name'])
                except:
                    print('asd')
                    continue
        scheduler = require("nonebot_plugin_apscheduler").scheduler
        scheduler.remove_job(hash)
    else:
        await send_Msg(str('{}\nHash: {} \n下载了 {}%\n平均下载速度：{} KB/s'.format(name, hash, round(
            info['total_downloaded'] / info['total_size'] * 100, 2), round(info['dl_speed_avg'] / 1024, 2))))


async def rss_trigger(hash: str, group_ids: list, name: str):
    scheduler = require("nonebot_plugin_apscheduler").scheduler
    # 制作一个“time分钟/次”触发器
    trigger = IntervalTrigger(
        # minutes=1,
        seconds=int(config.down_status_msg_date),
        jitter=10
    )
    job_defaults = {'max_instances': 10}
    # 添加任务
    scheduler.add_job(
        func=check_down_status,  # 要添加任务的函数，不要带参数
        trigger=trigger,  # 触发器
        args=(hash, group_ids, name),  # 函数的参数列表，注意：只有一个值时，不能省略末尾的逗号
        id=hash,
        # kwargs=None,
        misfire_grace_time=60,  # 允许的误差时间，建议不要省略
        # jobstore='default',  # 任务储存库，在下一小节中说明
        job_defaults=job_defaults,
    )
    await send_Msg(str('👏 {}\nHash: {} \n下载任务添加成功！'.format(name, hash)))
