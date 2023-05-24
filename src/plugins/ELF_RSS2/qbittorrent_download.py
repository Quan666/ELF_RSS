import asyncio
import base64
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiohttp
import arrow
from apscheduler.triggers.interval import IntervalTrigger
from nonebot import get_bot
from nonebot.adapters.onebot.v11 import ActionFailed, Bot, NetworkError
from nonebot.log import logger
from qbittorrent import Client

from .config import config
from .utils import (
    convert_size,
    get_bot_group_list,
    get_torrent_b16_hash,
    scheduler,
    send_message_to_admin,
)

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
async def send_msg(
    bot: Bot, msg: str, notice_group: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    logger.info(msg)
    msg_id = []
    group_list = await get_bot_group_list(bot)
    if down_status_msg_group := (notice_group or config.down_status_msg_group):
        for group_id in down_status_msg_group:
            if int(group_id) not in group_list:
                logger.error(f"Bot[{bot.self_id}]未加入群组[{group_id}]")
                continue
            msg_id.append(await bot.send_group_msg(group_id=int(group_id), message=msg))
    return msg_id


async def get_qb_client() -> Optional[Client]:
    try:
        qb = Client(config.qb_web_url)
        if config.qb_username and config.qb_password:
            qb.login(config.qb_username, config.qb_password)
        else:
            qb.login()
    except Exception:
        bot: Bot = get_bot()  # type: ignore
        msg = (
            "❌ 无法连接到 qbittorrent ，请检查：\n"
            "1. 是否启动程序\n"
            "2. 是否勾选了“Web用户界面（远程控制）”\n"
            "3. 连接地址、端口是否正确"
        )
        logger.exception(msg)
        await send_message_to_admin(msg, bot)
        return None
    try:
        qb.get_default_save_path()
    except Exception:
        bot: Bot = get_bot()  # type: ignore
        msg = "❌ 无法连登录到 qbittorrent ，请检查相关配置是否正确"
        logger.exception(msg)
        await send_message_to_admin(msg, bot)
        return None
    return qb


async def get_torrent_info_from_hash(
    bot: Bot, qb: Client, url: str, proxy: Optional[str]
) -> Dict[str, str]:
    info = None
    if re.search(r"magnet:\?xt=urn:btih:", url):
        qb.download_from_link(link=url)
        if _hash_str := re.search(r"[A-F\d]{40}", url, flags=re.I):
            hash_str = _hash_str[0].lower()
        else:
            hash_str = (
                base64.b16encode(
                    base64.b32decode(re.search(r"[2-7A-Z]{32}", url, flags=re.I)[0])  # type: ignore
                )
                .decode("utf-8")
                .lower()
            )

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
                await send_msg(bot, f"下载种子失败，可能需要代理\n{e}")
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
    bot: Bot, url: str, group_ids: List[str], name: str, proxy: Optional[str]
) -> str:
    qb = await get_qb_client()
    if not qb:
        return ""
    # 获取种子 hash
    info = await get_torrent_info_from_hash(bot=bot, qb=qb, url=url, proxy=proxy)
    await rss_trigger(
        bot,
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


async def update_down_status_message(
    bot: Bot, hash_str: str, info: Dict[str, Any], name: str
) -> List[Dict[str, Any]]:
    return await send_msg(
        bot,
        f"{name}\n"
        f"Hash：{hash_str}\n"
        f"下载了 {round(info['total_downloaded'] / info['total_size'] * 100, 2)}%\n"
        f"平均下载速度： {round(info['dl_speed_avg'] / 1024, 2)} KB/s",
    )


async def upload_files_to_groups(
    bot: Bot,
    group_ids: List[str],
    info: Dict[str, Any],
    files: List[Dict[str, Any]],
    name: str,
    hash_str: str,
) -> None:
    for group_id in group_ids:
        for tmp in files:
            path = Path(info.get("save_path", "")) / tmp["name"]
            if config.qb_down_path:
                if (_path := Path(config.qb_down_path)).is_dir():
                    path = _path / tmp["name"]

            await send_msg(bot, f"{name}\nHash：{hash_str}\n开始上传到群：{group_id}")

            try:
                await bot.call_api(
                    "upload_group_file",
                    group_id=group_id,
                    file=str(path),
                    name=tmp["name"],
                )
            except ActionFailed:
                msg = f"{name}\nHash：{hash_str}\n上传到群：{group_id}失败！请手动上传！"
                await send_msg(bot, msg, [group_id])
                logger.exception(msg)
            except (NetworkError, TimeoutError) as e:
                logger.warning(e)


# 检查下载状态
async def check_down_status(
    bot: Bot, hash_str: str, group_ids: List[str], name: str
) -> None:
    qb = await get_qb_client()
    if not qb:
        return
    # 防止中途删掉任务，无限执行
    try:
        info = qb.get_torrent(hash_str)
        files = qb.get_torrent_files(hash_str)
    except Exception as e:
        logger.exception(e)
        scheduler.remove_job(hash_str)
        return

    if info["total_downloaded"] - info["total_size"] >= 0.000000:
        all_time = arrow.now() - down_info[hash_str]["start_time"]
        await send_msg(
            bot,
            f"👏 {name}\n"
            f"Hash：{hash_str}\n"
            f"下载完成！耗时：{str(all_time).split('.', 2)[0]}",
        )
        down_info[hash_str]["status"] = DOWN_STATUS_UPLOADING

        await upload_files_to_groups(bot, group_ids, info, files, name, hash_str)

        scheduler.remove_job(hash_str)
        down_info[hash_str]["status"] = DOWN_STATUS_UPLOAD_OK
    else:
        await delete_msg(bot, down_info[hash_str]["downing_tips_msg_id"])
        msg_id = await update_down_status_message(bot, hash_str, info, name)
        down_info[hash_str]["downing_tips_msg_id"] = msg_id


# 撤回消息
async def delete_msg(bot: Bot, msg_ids: List[Dict[str, Any]]) -> None:
    for msg_id in msg_ids:
        await bot.delete_msg(message_id=msg_id["message_id"])


async def rss_trigger(bot: Bot, hash_str: str, group_ids: List[str], name: str) -> None:
    # 制作一个频率为“ n 秒 / 次”的触发器
    trigger = IntervalTrigger(seconds=int(config.down_status_msg_date), jitter=10)
    job_defaults = {"max_instances": 1}
    # 添加任务
    scheduler.add_job(
        func=check_down_status,  # 要添加任务的函数，不要带参数
        trigger=trigger,  # 触发器
        args=(bot, hash_str, group_ids, name),  # 函数的参数列表，注意：只有一个值时，不能省略末尾的逗号
        id=hash_str,
        misfire_grace_time=60,  # 允许的误差时间，建议不要省略
        job_defaults=job_defaults,
    )
    bot: Bot = get_bot()  # type: ignore
    await send_msg(bot, f"👏 {name}\nHash：{hash_str}\n下载任务添加成功！", group_ids)
