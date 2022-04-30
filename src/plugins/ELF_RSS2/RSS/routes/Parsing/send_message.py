import asyncio
from collections import defaultdict
from typing import Any, Dict, List

import nonebot
from nonebot.adapters import Bot
from nonebot.log import logger

from ....bot_info import (
    get_bot_friend_list,
    get_bot_group_list,
    get_bot_guild_channel_list,
)
from ....RSS.rss_class import Rss

sending_lock = defaultdict(asyncio.Lock)


# 发送消息
async def send_msg(rss: Rss, msg: str, item: Dict[str, Any]) -> bool:
    try:
        bot = nonebot.get_bot()
    except ValueError:
        return False
    if not msg:
        return False
    flag = False
    error_msg = f"消息发送失败，已达最大重试次数！\n链接：[{item.get('link')}]"
    if rss.user_id:
        friend_list = await get_bot_friend_list(bot)
        if invalid_user_id_list := [
            user_id for user_id in rss.user_id if int(user_id) not in friend_list
        ]:
            logger.error(
                f"QQ号[{','.join(invalid_user_id_list)}]不是Bot[{bot.self_id}]的好友"
                f" 链接：[{item.get('link')}]"
            )
        flag = all(
            await asyncio.gather(
                *[
                    send_private_msg(bot, msg, int(user_id), item, error_msg)
                    for user_id in rss.user_id
                    if int(user_id) in friend_list
                ]
            )
        )
    if rss.group_id:
        group_list = await get_bot_group_list(bot)
        if invalid_group_id_list := [
            group_id for group_id in rss.group_id if int(group_id) not in group_list
        ]:
            logger.error(
                f"Bot[{bot.self_id}]未加入群组[{','.join(invalid_group_id_list)}]"
                f" 链接：[{item.get('link')}]"
            )
        flag = all(
            await asyncio.gather(
                *[
                    send_group_msg(bot, msg, int(group_id), item, error_msg)
                    for group_id in rss.group_id
                    if int(group_id) in group_list
                ]
            )
        )
    if rss.guild_channel_id:
        valid_guild_channel_id_list = await filter_valid_guild_channel_id_list(
            bot=bot, guild_channel_id_list=rss.guild_channel_id, item=item
        )
        flag = all(
            await asyncio.gather(
                *[
                    send_guild_channel_msg(bot, msg, guild_channel_id, item, error_msg)
                    for guild_channel_id in valid_guild_channel_id_list
                ]
            )
        )
    return flag


# 发送私聊消息
async def send_private_msg(
    bot: Bot, msg: str, user_id: int, item: Dict[str, Any], error_msg: str
) -> bool:
    flag = False
    while True:
        async with sending_lock[(user_id, "private")]:
            try:
                await bot.send_private_msg(user_id=user_id, message=msg)
                flag = True
            except Exception as e:
                logger.error(f"E: {repr(e)} 链接：[{item.get('link')}]")
                if item.get("count") == 3:
                    await bot.send_private_msg(
                        user_id=user_id, message=f"{error_msg}\nE: {repr(e)}"
                    )
            return flag


# 发送群聊消息
async def send_group_msg(
    bot: Bot, msg: str, group_id: int, item: Dict[str, Any], error_msg: str
) -> bool:
    flag = False
    while True:
        async with sending_lock[(group_id, "group")]:
            try:
                await bot.send_group_msg(group_id=group_id, message=msg)
                flag = True
            except Exception as e:
                logger.error(f"E: {repr(e)} 链接：[{item.get('link')}]")
                if item.get("count") == 3:
                    await bot.send_group_msg(
                        group_id=group_id, message=f"E: {repr(e)}\n{error_msg}"
                    )
            return flag


# 过滤合法频道
async def filter_valid_guild_channel_id_list(
    bot: Bot, guild_channel_id_list: List[str], item: Dict[str, Any]
) -> List[str]:
    valid_guild_channel_id_list = []
    for guild_channel_id in guild_channel_id_list:
        guild_id, channel_id = guild_channel_id.split("@")
        guild_list = await get_bot_guild_channel_list(bot)
        if guild_id not in guild_list:
            guild_name = (await bot.get_guild_meta_by_guest(guild_id=guild_id))[
                "guild_name"
            ]
            logger.error(
                f"Bot[{bot.self_id}]未加入频道 {guild_name}[{guild_id}] 链接：[{item.get('link')}]"
            )
            continue

        channel_list = await get_bot_guild_channel_list(bot, guild_id=guild_id)
        if channel_id not in channel_list:
            guild_name = (await bot.get_guild_meta_by_guest(guild_id=guild_id))[
                "guild_name"
            ]
            logger.error(
                f"Bot[{bot.self_id}]未加入频道 {guild_name}[{guild_id}]的子频道[{channel_id}] 链接：[{item.get('link')}]"
            )
            continue
        valid_guild_channel_id_list.append(guild_channel_id)
    return valid_guild_channel_id_list


# 发送频道消息
async def send_guild_channel_msg(
    bot: Bot,
    msg: str,
    guild_channel_id: str,
    item: Dict[str, Any],
    error_msg: str,
) -> bool:
    flag = False
    guild_id, channel_id = guild_channel_id.split("@")
    while True:
        async with sending_lock[(guild_channel_id, "guild_channel")]:
            try:
                await bot.send_guild_channel_msg(
                    message=msg, guild_id=guild_id, channel_id=channel_id
                )
                flag = True
            except Exception as e:
                logger.error(f"E: {repr(e)} 链接：[{item.get('link')}]")
                if item.get("count") == 3:
                    await bot.send_guild_channel_msg(
                        message=f"E: {repr(e)}\n{error_msg}",
                        guild_id=guild_id,
                        channel_id=channel_id,
                    )
            return flag
