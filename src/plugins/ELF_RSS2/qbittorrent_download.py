import asyncio
import base64
import re
from typing import Any, Dict, List, Optional

import aiohttp
import arrow
import nonebot
from apscheduler.triggers.interval import IntervalTrigger
from nonebot import require
from nonebot.adapters.onebot.v11 import ActionFailed
from nonebot.log import logger
from qbittorrent import Client

from .config import config
from .utils import convert_size, get_bot_group_list

# 计划
# 创建一个全局定时器用来检测种子下载情况
# 群文件上传成功回调
# 文件三种状态1.下载中2。上传中3.上传完成
# 文件信息持久化存储
# 关键词正则表达式
# 下载开关

DOWN_STATUS_DOWNING = 1  # 下载中
DOWN_STATUS_UPLOADING = 2  # 上传中
DOWN_STATUS_UPLOAD_OK = 3  # 上传完成
down_info: Dict[str, Dict[str, Any]] = {}

# 示例
# {
#     "hash值": {
#         "status":DOWN_STATUS_DOWNING,
#         "start_time":None, # 下载开始时间
#         "downing_tips_msg_id":[] # 下载中通知群上一条通知的信息，用于撤回，防止刷屏
#     }
# }


# 发送通知
async def send_msg(msg: str) -> List[Dict[str, Any]]:
    logger.info(msg)
    bot = nonebot.get_bot()
    msg_id = []
    group_list = await get_bot_group_list(bot)
    if config.down_status_msg_group:
        for group_id in config.down_status_msg_group:
            if int(group_id) not in group_list:
                logger.error(f"Bot[{bot.self_id}]未加入群组[{group_id}]")
                continue
            msg_id.append(await bot.send_group_msg(group_id=group_id, message=msg))
    return msg_id


async def get_qb_client() -> Optional[Client]:
    try:
        qb = Client(config.qb_web_url)
        if config.qb_username and config.qb_password:
            qb.login(config.qb_username, config.qb_password)
        else:
            qb.login()
    except Exception:
        bot = nonebot.get_bot()
        msg = (
            "❌ 无法连接到 qbittorrent ，请检查：\n"
            "1. 是否启动程序\n"
            "2. 是否勾选了“Web用户界面（远程控制）”\n"
            "3. 连接地址、端口是否正确"
        )
        logger.exception(msg)
        await bot.send_private_msg(user_id=str(list(config.superusers)[0]), message=msg)
        return None
    try:
        qb.get_default_save_path()
    except Exception:
        bot = nonebot.get_bot()
        msg = "❌ 无法连登录到 qbittorrent ，请检查相关配置是否正确"
        logger.exception(msg)
        await bot.send_private_msg(user_id=str(list(config.superusers)[0]), message=msg)
        return None
    return qb


def get_torrent_b16_hash(content: bytes) -> str:
    import magneturi

    # mangetlink = magneturi.from_torrent_file(torrentname)
    manget_link = magneturi.from_torrent_data(content)
    # print(mangetlink)
    ch = ""
    n = 20
    b32_hash = n * ch + manget_link[20:52]
    # print(b32Hash)
    b16_hash = base64.b16encode(base64.b32decode(b32_hash))
    b16_hash = b16_hash.lower()
    # print("40位info hash值：" + '\n' + b16Hash)
    # print("磁力链：" + '\n' + "magnet:?xt=urn:btih:" + b16Hash)
    return str(b16_hash, "utf-8")


async def get_torrent_info_from_hash(
    qb: Client, url: str, proxy: Optional[str]
) -> Dict[str, str]:
    info = None
    if re.search(r"magnet:\?xt=urn:btih:", url):
        qb.download_from_link(link=url)
        hash_str = re.search("[A-Fa-f0-9]{40}", url)[0]  # type: ignore
    else:
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=100)
        ) as session:
            try:
                resp = await session.get(url, proxy=proxy)
                content = await resp.read()
                qb.download_from_file(content)
                hash_str = get_torrent_b16_hash(content)
            except Exception as e:
                await send_msg(f"下载种子失败，可能需要代理\n{e}")
                return {}

    while not info:
        for tmp_torrent in qb.torrents():
            if tmp_torrent["hash"] == hash_str and tmp_torrent["size"]:
                info = {
                    "hash": tmp_torrent["hash"],
                    "filename": tmp_torrent["name"],
                    "size": convert_size(tmp_torrent["size"]),
                }
        await asyncio.sleep(1)
    return info


# 种子地址，种子下载路径，群文件上传 群列表，订阅名称
async def start_down(
    url: str, group_ids: List[str], name: str, proxy: Optional[str]
) -> str:
    qb = await get_qb_client()
    if not qb:
        return ""
    # 获取种子 hash
    info = await get_torrent_info_from_hash(qb=qb, url=url, proxy=proxy)
    await rss_trigger(
        hash_str=info["hash"],
        group_ids=group_ids,
        name=f"订阅：{name}\n{info['filename']}\n文件大小：{info['size']}",
    )
    down_info[info["hash"]] = {
        "status": DOWN_STATUS_DOWNING,
        "start_time": arrow.now(),  # 下载开始时间
        "downing_tips_msg_id": [],  # 下载中通知群上一条通知的信息，用于撤回，防止刷屏
    }
    return info["hash"]


# 检查下载状态
async def check_down_status(hash_str: str, group_ids: List[str], name: str) -> None:
    qb = await get_qb_client()
    if not qb:
        return
    info = qb.get_torrent(hash_str)
    files = qb.get_torrent_files(hash_str)
    bot = nonebot.get_bot()
    if info["total_downloaded"] - info["total_size"] >= 0.000000:
        all_time = arrow.now() - down_info[hash_str]["start_time"]
        await send_msg(
            f"👏 {name}\n"
            f"Hash：{hash_str}\n"
            f"下载完成！耗时：{str(all_time).split('.', 2)[0]}"
        )
        down_info[hash_str]["status"] = DOWN_STATUS_UPLOADING
        for group_id in group_ids:
            for tmp in files:
                # 异常包起来防止超时报错导致后续不执行
                try:
                    if config.qb_down_path and len(config.qb_down_path) > 0:
                        path = config.qb_down_path + tmp["name"]
                    else:
                        path = info["save_path"] + tmp["name"]
                    await send_msg(f"{name}\nHash：{hash_str}\n开始上传到群：{group_id}")
                    try:
                        await bot.call_api(
                            "upload_group_file",
                            group_id=group_id,
                            file=path,
                            name=tmp["name"],
                        )
                    except ActionFailed:
                        msg = f"{name}\nHash：{hash_str}\n上传到群：{group_id}失败！请手动上传！"
                        await send_msg(msg)
                        logger.exception(msg)
                except TimeoutError as e:
                    logger.warning(e)
        scheduler = require("nonebot_plugin_apscheduler").scheduler
        scheduler.remove_job(hash_str)
        down_info[hash_str]["status"] = DOWN_STATUS_UPLOAD_OK
    else:
        await delete_msg(down_info[hash_str]["downing_tips_msg_id"])
        msg_id = await send_msg(
            f"{name}\n"
            f"Hash：{hash_str}\n"
            f"下载了 {round(info['total_downloaded'] / info['total_size'] * 100, 2)}%\n"
            f"平均下载速度： {round(info['dl_speed_avg'] / 1024, 2)} KB/s"
        )
        down_info[hash_str]["downing_tips_msg_id"] = msg_id


# 撤回消息
async def delete_msg(msg_ids: List[Dict[str, Any]]) -> None:
    bot = nonebot.get_bot()
    for msg_id in msg_ids:
        await bot.call_api("delete_msg", message_id=msg_id["message_id"])


async def rss_trigger(hash_str: str, group_ids: List[str], name: str) -> None:
    scheduler = require("nonebot_plugin_apscheduler").scheduler
    # 制作一个频率为“ n 秒 / 次”的触发器
    trigger = IntervalTrigger(seconds=int(config.down_status_msg_date), jitter=10)
    job_defaults = {"max_instances": 1}
    # 添加任务
    scheduler.add_job(
        func=check_down_status,  # 要添加任务的函数，不要带参数
        trigger=trigger,  # 触发器
        args=(hash_str, group_ids, name),  # 函数的参数列表，注意：只有一个值时，不能省略末尾的逗号
        id=hash_str,
        misfire_grace_time=60,  # 允许的误差时间，建议不要省略
        job_defaults=job_defaults,
    )
    await send_msg(f"👏 {name}\nHash：{hash_str}\n下载任务添加成功！")
