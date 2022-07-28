import asyncio
from collections import defaultdict
from contextlib import suppress
from typing import Any, DefaultDict, Dict, Tuple, Union

import arrow
from nonebot import get_bot
from nonebot.adapters.onebot.v11 import Bot
from nonebot.log import logger

from ..rss_class import Rss

sending_lock: DefaultDict[Tuple[Union[int, str], str], asyncio.Lock] = defaultdict(
    asyncio.Lock
)


# 发送消息
async def send_msg(rss: Rss, msg: str, item: Dict[str, Any]) -> bool:
    try:
        bot: Bot = get_bot()  # type: ignore
    except ValueError:
        return False
    if not msg:
        return False
    flag = False
    error_msg = f"消息发送失败！\n链接：[{item.get('link')}]"
    if rss.user_id:
        flag = any(
            await asyncio.gather(
                *[
                    send_private_msg(bot, msg, int(user_id), item, error_msg)
                    for user_id in rss.user_id
                ]
            )
        )
    if rss.group_id:
        flag = (
            any(
                await asyncio.gather(
                    *[
                        send_group_msg(bot, msg, int(group_id), item, error_msg)
                        for group_id in rss.group_id
                    ]
                )
            )
            or flag
        )
    if rss.guild_channel_id:
        flag = (
            any(
                await asyncio.gather(
                    *[
                        send_guild_channel_msg(
                            bot, msg, guild_channel_id, item, error_msg
                        )
                        for guild_channel_id in rss.guild_channel_id
                    ]
                )
            )
            or flag
        )
    return flag


# 发送私聊消息
async def send_private_msg(
    bot: Bot, msg: str, user_id: int, item: Dict[str, Any], error_msg: str
) -> bool:
    flag = False
    start_time = arrow.now()
    async with sending_lock[(user_id, "private")]:
        try:
            await bot.send_private_msg(user_id=user_id, message=msg)
            await asyncio.sleep(max(1 - (arrow.now() - start_time).total_seconds(), 0))
            flag = True
        except Exception as e:
            logger.error(f"E: {repr(e)}\n链接：[{item.get('link')}]")
            if item.get("to_send"):
                flag = True
                with suppress(Exception):
                    await bot.send_private_msg(
                        user_id=user_id, message=f"{error_msg}\nE: {repr(e)}"
                    )
        return flag


# 发送群聊消息
async def send_group_msg(
    bot: Bot, msg: str, group_id: int, item: Dict[str, Any], error_msg: str
) -> bool:
    flag = False
    start_time = arrow.now()
    async with sending_lock[(group_id, "group")]:
        try:
            await bot.send_group_msg(group_id=group_id, message=msg)
            await asyncio.sleep(max(1 - (arrow.now() - start_time).total_seconds(), 0))
            flag = True
        except Exception as e:
            logger.error(f"E: {repr(e)}\n链接：[{item.get('link')}]")
            if item.get("to_send"):
                flag = True
                with suppress(Exception):
                    await bot.send_group_msg(
                        group_id=group_id, message=f"E: {repr(e)}\n{error_msg}"
                    )
        return flag


# 发送频道消息
async def send_guild_channel_msg(
    bot: Bot,
    msg: str,
    guild_channel_id: str,
    item: Dict[str, Any],
    error_msg: str,
) -> bool:
    flag = False
    start_time = arrow.now()
    guild_id, channel_id = guild_channel_id.split("@")
    async with sending_lock[(guild_channel_id, "guild_channel")]:
        try:
            await bot.send_guild_channel_msg(
                message=msg, guild_id=guild_id, channel_id=channel_id
            )
            await asyncio.sleep(max(1 - (arrow.now() - start_time).total_seconds(), 0))
            flag = True
        except Exception as e:
            logger.error(f"E: {repr(e)}\n链接：[{item.get('link')}]")
            if item.get("to_send"):
                flag = True
                with suppress(Exception):
                    await bot.send_guild_channel_msg(
                        message=f"E: {repr(e)}\n{error_msg}",
                        guild_id=guild_id,
                        channel_id=channel_id,
                    )
        return flag
