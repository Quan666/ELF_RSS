import asyncio
import base64
import datetime
import time

import httpx
import nonebot
from apscheduler.triggers.interval import IntervalTrigger
from nonebot import logger, require
from qbittorrent import Client
# from starlette.responses import FileResponse
from ..config import config

# 计划
# 创建一个全局定时器用来检测种子下载情况
# 群文件上传成功回调
# 文件三种状态1.下载中2。上传中3.上传完成
# 文件信息持久化存储
# 关键词正则表达式
# 下载开关


# app = nonebot.get_asgi()


# @app.get("/elfrss/file/{filename}",include_in_schema=False)
# async def file(filename: str) -> FileResponse:
#     path = (await get_qb()).get_default_save_path()
#     return FileResponse(path=path + os.sep + filename, filename=filename)

DOWN_STATUS_DOWNING = 1  # 下载中
DOWN_STATUS_UPLOADING = 2  # 上传中
DOWN_STATUS_UPLOADOK = 3  # 上传完成
down_info = {}


# 示例
# {
#     "hash值": {
#         "status":DOWN_STATUS_DOWNING,
#         "start_time":None, # 下载开始时间
#         "downing_tips_msg_id":[] # 下载中通知群上一条通知的信息，用于撤回，防止刷屏
#     }
# }

# 发送通知
async def send_Msg(msg: str) -> list:
    logger.info(msg)
    bot, = nonebot.get_bots().values()
    msg_id = []
    for group_id in config.down_status_msg_group:
        msg_id.append(await bot.send_msg(message_type='group', group_id=int(group_id), message=msg))
    return msg_id


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


def getSize(size: int) -> str:
    kb = 1024
    mb = kb * 1024
    gb = mb * 1024
    tb = gb * 1024

    if size >= tb:
        return "%.2f TB" % float(size / tb)
    if size >= gb:
        return "%.2f GB" % float(size / gb)
    if size >= mb:
        return "%.2f MB" % float(size / mb)
    if size >= kb:
        return "%.2f KB" % float(size / kb)


def get_torrent_b16Hash(content: bytes) -> str:
    import magneturi
    # mangetlink = magneturi.from_torrent_file(torrentname)
    mangetlink = magneturi.from_torrent_data(content)
    # print(mangetlink)
    ch = ''
    n = 20
    b32Hash = n * ch + mangetlink[20:52]
    # print(b32Hash)
    b16Hash = base64.b16encode(base64.b32decode(b32Hash))
    b16Hash = b16Hash.lower()
    b16Hash = str(b16Hash, "utf-8")
    # print("40位info hash值：" + '\n' + b16Hash)
    # print("磁力链：" + '\n' + "magnet:?xt=urn:btih:" + b16Hash)
    return b16Hash


async def get_Hash_Name(url: str, proxy=None) -> dict:
    if not proxy:
        proxy = {}
    qb = await get_qb()
    info = None
    async with httpx.AsyncClient(proxies=proxy) as client:
        try:
            res = await client.get(url, timeout=100)
            qb.download_from_file(res.content)
            hash = get_torrent_b16Hash(res.content)
            while not info:
                for tmp_torrent in qb.torrents():
                    if tmp_torrent['hash'] == hash:
                        info = {
                            'hash': tmp_torrent['hash'],
                            'filename': tmp_torrent['name'],
                            'size': getSize(tmp_torrent['size'])
                        }
                await asyncio.sleep(1)
        except Exception as e:
            await send_Msg('下载种子失败,可能需要代理:{}'.format(e))
    return info


# 种子地址，种子下载路径，群文件上传 群列表，订阅名称
async def start_down(url: str, path: str, group_ids: list, name: str, proxy=None)->str:
    qb = await get_qb()
    if not qb:
        return
    # 获取种子 hash
    info = await get_Hash_Name(url=url, proxy=proxy)
    await rss_trigger(hash=info['hash'], group_ids=group_ids,
                      name='订阅：{}\n{}\n文件大小：{}'.format(name, info['filename'], info['size']))
    down_info[info['hash']] = {
        "status": DOWN_STATUS_DOWNING,
        "start_time": datetime.datetime.now(),  # 下载开始时间
        "downing_tips_msg_id": []  # 下载中通知群上一条通知的信息，用于撤回，防止刷屏
    }
    return info['hash']

# 检查下载状态
async def check_down_status(hash: str, group_ids: list, name: str):
    qb = await get_qb()
    if not qb:
        return
    info = qb.get_torrent(hash)
    files = qb.get_torrent_files(hash)
    bot, = nonebot.get_bots().values()
    if info['total_downloaded'] - info['total_size'] >= 0.000000:
        all_time = (datetime.datetime.now() - down_info[hash]['start_time']).seconds
        await send_Msg(str('👏 {}\nHash: {} \n下载完成！耗时：{} s'.format(name, hash, str(all_time))))
        down_info[hash]['status'] = DOWN_STATUS_UPLOADING
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
                    continue
        scheduler = require("nonebot_plugin_apscheduler").scheduler
        scheduler.remove_job(hash)
        down_info[hash]['status'] = DOWN_STATUS_UPLOADOK
    else:
        await delete_msg(down_info[hash]['downing_tips_msg_id'])
        msg_id = await send_Msg(str('{}\nHash: {} \n下载了 {}%\n平均下载速度：{} KB/s'.format(name, hash, round(
            info['total_downloaded'] / info['total_size'] * 100, 2), round(info['dl_speed_avg'] / 1024, 2))))
        down_info[hash]['downing_tips_msg_id'] = msg_id


# 撤回消息
async def delete_msg(msg_ids: list):
    bot, = nonebot.get_bots().values()
    for msg_id in msg_ids:
        await bot.call_api('delete_msg',message_id=msg_id['message_id'])


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
