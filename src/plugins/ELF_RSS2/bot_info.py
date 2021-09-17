from nonebot.adapters.cqhttp import Bot
from typing import List


async def get_bot_qq(bot: Bot) -> int:
    return (await bot.get_login_info())["user_id"]


async def get_bot_friend_list(bot: Bot) -> List[int]:
    return list(map(lambda x: x["user_id"], await bot.get_friend_list()))


async def get_bot_group_list(bot: Bot) -> List[int]:
    return list(map(lambda x: x["group_id"], await bot.get_group_list()))
