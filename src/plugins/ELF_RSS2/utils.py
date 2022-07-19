import base64
import math
from typing import Any, Dict, List, Mapping, Optional

import nonebot
from nonebot.adapters.onebot.v11.bot import Bot
from nonebot.log import logger

from .config import config


def get_http_caching_headers(
    headers: Optional[Mapping[str, Any]],
) -> Dict[str, Optional[str]]:
    return (
        {
            "Last-Modified": headers.get("Last-Modified") or headers.get("Date"),
            "ETag": headers.get("ETag"),
        }
        if headers
        else {"Last-Modified": None, "ETag": None}
    )


def convert_size(size_bytes: int) -> str:
    if size_bytes == 0:
        return "0 B"
    size_name = ("B", "KB", "MB", "GB", "TB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_name[i]}"


async def get_bot_friend_list(bot: Bot) -> List[int]:
    friend_list = await bot.get_friend_list()
    return [i["user_id"] for i in friend_list]


async def get_bot_group_list(bot: Bot) -> List[int]:
    group_list = await bot.get_group_list()
    return [i["group_id"] for i in group_list]


async def get_bot_guild_channel_list(
    bot: Bot, guild_id: Optional[str] = None
) -> List[str]:
    guild_list = await bot.get_guild_list()
    if guild_id is None:
        return [i["guild_id"] for i in guild_list]
    if guild_id in [i["guild_id"] for i in guild_list]:
        channel_list = await bot.get_guild_channel_list(guild_id=guild_id)
        return [i["channel_id"] for i in channel_list]
    return []


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


async def send_message_to_admin(message: str) -> None:
    bot = nonebot.get_bot()
    await bot.send_private_msg(user_id=str(list(config.superusers)[0]), message=message)


async def send_msg(
    msg: str,
    user_ids: Optional[List[str]] = None,
    group_ids: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """
    msg: str
    user: List[str]
    group: List[str]

    发送消息到私聊或群聊
    """
    bot = nonebot.get_bot()
    msg_id = []
    if group_ids:
        group_list = await get_bot_group_list(bot)  # type: ignore
        for group_id in group_ids:
            if int(group_id) not in group_list:
                logger.error(f"Bot[{bot.self_id}]未加入群组[{group_id}]")
                continue
            msg_id.append(await bot.send_group_msg(group_id=group_id, message=msg))
    if user_ids:
        user_list = await get_bot_friend_list(bot)  # type: ignore
        for user_id in user_ids:
            if int(user_id) not in user_list:
                logger.error(f"Bot[{bot.self_id}]未加入好友[{user_id}]")
                continue
            msg_id.append(await bot.send_private_msg(user_id=user_id, message=msg))
    return msg_id
