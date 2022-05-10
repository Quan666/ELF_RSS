import re
from typing import Any

import nonebot
from nonebot import on_command
from nonebot.adapters.onebot.v11 import (
    Event,
    GroupMessageEvent,
    Message,
    PrivateMessageEvent,
)
from nonebot.log import logger
from nonebot.params import CommandArg
from nonebot.rule import to_me
from qbittorrent import Client

from ..config import config
from ..utils import convert_size

upload_group_file = on_command(
    "upload_file",
    aliases={"uploadfile"},
    rule=to_me(),
    priority=5,
)


async def get_qb() -> Any:
    try:
        qb = Client(config.qb_web_url)
        qb.login()
    except Exception:
        msg = (
            "❌ 无法连接到 qbittorrent ，请检查：\n"
            "1. 是否启动程序\n"
            '2. 是否勾选了 "Web用户界面（远程控制）"\n'
            "3. 连接地址、端口是否正确"
        )
        logger.exception(msg)
        await upload_group_file.send(msg)
        return None
    try:
        qb.get_default_save_path()
    except Exception:
        msg = "❌ 无法连登录到 qbittorrent ，请检查是否勾选“对本地主机上的客户端跳过身份验证”"
        logger.exception(msg)
        await upload_group_file.send(msg)
        return None
    return qb


# 检查下载状态
async def check_down_status(hash_str: str, group_id: int) -> None:
    qb = await get_qb()
    if not qb:
        return
    info = qb.get_torrent(hash_str)
    files = qb.get_torrent_files(hash_str)
    bot = nonebot.get_bot()
    if info["total_downloaded"] - info["total_size"] >= 0.000000:
        for tmp in files:
            # 异常包起来防止超时报错导致后续不执行
            try:
                if config.qb_down_path and len(config.qb_down_path) > 0:
                    path = config.qb_down_path + tmp["name"]
                else:
                    path = info["save_path"] + tmp["name"]
                await upload_group_file.send(
                    f"{tmp['name']}\n"
                    f"大小：{convert_size(info['total_size'])}\n"
                    f"Hash: {hash_str}\n"
                    "开始上传"
                )
                await bot.upload_group_file(
                    group_id=group_id, file=path, name=tmp["name"]
                )
            except Exception:
                pass
    else:
        await upload_group_file.send(
            f"Hash: {hash_str}\n"
            f"下载了 {round(info['total_downloaded'] / info['total_size'] * 100, 2)}%\n"
            f"平均下载速度：{round(info['dl_speed_avg'] / 1024, 2)} KB/s"
        )


@upload_group_file.handle()
async def handle_first_receive(event: Event, message: Message = CommandArg()) -> None:
    hash_str = re.search("[a-f0-9]{40}", str(message))[0]  # type: ignore
    group_id = None
    if isinstance(event, PrivateMessageEvent):
        group_id = int(re.search("[0-9]{6,12}", str(message).replace(hash_str, ""))[0])  # type: ignore
    elif isinstance(event, GroupMessageEvent):
        group_id = event.group_id
    if group_id:
        await check_down_status(hash_str=hash_str, group_id=group_id)
