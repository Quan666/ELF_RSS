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
        flag = await send_private_msg(bot, msg, rss.user_id, item, error_msg)
    if rss.group_id:
        flag = await send_group_msg(bot, msg, rss.group_id, item, error_msg)
    if rss.guild_channel_id:
        flag = await send_guild_channel_msg(
            bot, msg, rss.guild_channel_id, item, error_msg
        )
    return flag


# 发送私聊消息
async def send_private_msg(
    bot: Bot, msg: str, rss_user_id: List[str], item: Dict[str, Any], error_msg: str
) -> bool:
    flag = False
    friend_list = await get_bot_friend_list(bot)
    for user_id in rss_user_id:
        if int(user_id) not in friend_list:
            logger.error(
                f"QQ号[{user_id}]不是Bot[{bot.self_id}]的好友 链接：[{item.get('link')}]"
            )
            continue
        try:
            await bot.send_private_msg(user_id=int(user_id), message=msg)
            flag = True
        except Exception as e:
            logger.error(f"E: {repr(e)} 链接：[{item.get('link')}]")
            if item.get("count") == 3:
                await bot.send_private_msg(
                    user_id=int(user_id), message=f"{error_msg}\nE: {repr(e)}"
                )
    return flag


# 发送群聊消息
async def send_group_msg(
    bot: Bot, msg: str, rss_group_id: List[str], item: Dict[str, Any], error_msg: str
) -> bool:
    flag = False
    group_list = await get_bot_group_list(bot)
    for group_id in rss_group_id:
        if int(group_id) not in group_list:
            logger.error(f"Bot[{bot.self_id}]未加入群组[{group_id}] 链接：[{item.get('link')}]")
            continue
        try:
            await bot.send_group_msg(group_id=int(group_id), message=msg)
            flag = True
        except Exception as e:
            logger.error(f"E: {repr(e)} 链接：[{item.get('link')}]")
            if item.get("count") == 3:
                await bot.send_group_msg(
                    group_id=int(group_id), message=f"E: {repr(e)}\n{error_msg}"
                )
    return flag


# 发送频道消息
async def send_guild_channel_msg(
    bot: Bot,
    msg: str,
    rss_guild_channel_id: List[str],
    item: Dict[str, Any],
    error_msg: str,
) -> bool:
    flag = False
    for guild_channel_id in rss_guild_channel_id:
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
