import asyncio
from collections import defaultdict
from contextlib import suppress
from typing import Any, Callable, Coroutine, DefaultDict, Dict, List, Tuple, Union

import arrow
from nonebot import get_bot
from nonebot.adapters.onebot.v11 import Bot
from nonebot.log import logger

from ..config import config
from ..rss_class import Rss
from .cache_manage import insert_into_cache_db, write_item

sending_lock: DefaultDict[Tuple[Union[int, str], str], asyncio.Lock] = defaultdict(
    asyncio.Lock
)


# 发送消息
async def send_msg(
    rss: Rss, messages: List[str], items: List[Dict[str, Any]], header_message: str
) -> bool:
    try:
        bot: Bot = get_bot()  # type: ignore
    except ValueError:
        return False
    if not messages:
        return False
    flag = False
    if rss.user_id:
        flag = any(
            await asyncio.gather(
                *[
                    send_private_msg(bot, messages, int(user_id), items, header_message)
                    for user_id in rss.user_id
                ]
            )
        )
    if rss.group_id:
        flag = (
            any(
                await asyncio.gather(
                    *[
                        send_group_msg(
                            bot, messages, int(group_id), items, header_message
                        )
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
                            bot, messages, guild_channel_id, items, header_message
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
    bot: Bot,
    message: List[str],
    user_id: int,
    items: List[Dict[str, Any]],
    header_message: str,
) -> bool:
    return await send_msgs_with_lock(
        bot=bot,
        messages=message,
        target_id=user_id,
        target_type="private",
        items=items,
        header_message=header_message,
        send_func=lambda user_id, message: bot.send_private_msg(
            user_id=user_id, message=message  # type: ignore
        ),
    )


# 发送群聊消息
async def send_group_msg(
    bot: Bot,
    message: List[str],
    group_id: int,
    items: List[Dict[str, Any]],
    header_message: str,
) -> bool:
    return await send_msgs_with_lock(
        bot=bot,
        messages=message,
        target_id=group_id,
        target_type="group",
        items=items,
        header_message=header_message,
        send_func=lambda group_id, message: bot.send_group_msg(
            group_id=group_id, message=message  # type: ignore
        ),
    )


# 发送频道消息
async def send_guild_channel_msg(
    bot: Bot,
    message: List[str],
    guild_channel_id: str,
    items: List[Dict[str, Any]],
    header_message: str,
) -> bool:
    guild_id, channel_id = guild_channel_id.split("@")
    return await send_msgs_with_lock(
        bot=bot,
        messages=message,
        target_id=guild_channel_id,
        target_type="guild_channel",
        items=items,
        header_message=header_message,
        send_func=lambda guild_channel_id, message: bot.send_guild_channel_msg(
            message=message, guild_id=guild_id, channel_id=channel_id
        ),
    )


async def send_msgs_with_lock(
    bot: Bot,
    messages: List[str],
    target_id: Union[int, str],
    target_type: str,
    items: List[Dict[str, Any]],
    header_message: str,
    send_func: Callable[[Union[int, str], str], Coroutine[Any, Any, Dict[str, Any]]],
) -> bool:
    flag = False
    start_time = arrow.now()
    async with sending_lock[(target_id, target_type)]:
        try:
            if len(messages) == 1:
                await send_func(
                    target_id,
                    f"{header_message}\n----------------------\n{messages[0]}",
                )
            elif target_type != "guild_channel":
                await bot.send_forward_msg(
                    user_id=target_id if target_type == "private" else 0,
                    group_id=target_id if target_type == "group" else 0,
                    messages=handle_forward_message(bot, [header_message] + messages),
                )
            else:
                for message, item in zip(messages, items):
                    await send_msgs_with_lock(
                        bot,
                        [message],
                        target_id,
                        target_type,
                        [item],
                        header_message,
                        send_func,
                    )
            await asyncio.sleep(max(1 - (arrow.now() - start_time).total_seconds(), 0))
            flag = True
        except Exception as e:
            if len(messages) > 1 and target_type != "guild_channel":
                for message, item in zip(messages, items):
                    await send_msgs_with_lock(
                        bot,
                        [message],
                        target_id,
                        target_type,
                        [item],
                        header_message,
                        send_func,
                    )
            else:
                error_msg = f"E: {repr(e)}\n消息发送失败！\n链接：[{items[0].get('link')}]"
                logger.error(error_msg)
                if items[0].get("to_send"):
                    flag = True
                    with suppress(Exception):
                        await send_func(target_id, error_msg)
        return flag


def handle_forward_message(bot: Bot, messages: List[str]) -> List[Dict[str, Any]]:
    return [
        {
            "type": "node",
            "data": {
                "name": list(config.nickname)[0] if config.nickname else "\u200b",
                "uin": bot.self_id,
                "content": message,
            },
        }
        for message in messages
    ]


# 发送消息并写入文件
async def handle_send_msgs(
    rss: Rss, messages: List[str], items: List[Dict[str, Any]], state: Dict[str, Any]
) -> None:
    db = state["tinydb"]
    header_message = state["header_message"]

    if await send_msg(rss, messages, items, header_message):
        if rss.duplicate_filter_mode:
            for item in items:
                insert_into_cache_db(
                    conn=state["conn"], item=item, image_hash=item["image_hash"]
                )

        for item in items:
            if item.get("to_send"):
                item.pop("to_send")

    else:
        for item in items:
            item["to_send"] = True

    for item in items:
        write_item(db, item)
