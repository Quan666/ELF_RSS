import math
from typing import List, Optional

from nonebot.adapters import Bot


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
