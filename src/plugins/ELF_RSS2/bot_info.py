from nonebot.adapters.cqhttp import Bot
from typing import List


async def get_bot_qq(bot: Bot) -> int:
    login_info = await bot.get_login_info()
    return login_info["user_id"]


async def get_bot_friend_list(bot: Bot) -> List[int]:
    friend_list = await bot.get_friend_list()
    return [i["user_id"] for i in friend_list]


async def get_bot_group_list(bot: Bot) -> List[int]:
    group_list = await bot.get_group_list()
    return [i["group_id"] for i in group_list]
