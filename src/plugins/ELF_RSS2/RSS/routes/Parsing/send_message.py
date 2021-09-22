import nonebot

from nonebot import logger
from nonebot.adapters.cqhttp import NetworkError

from ....RSS import rss_class
from ....bot_info import get_bot_qq, get_bot_friend_list, get_bot_group_list


# 发送消息
async def send_msg(rss: rss_class.Rss, msg: str, item: dict) -> bool:
    bot = nonebot.get_bot()
    flag = False
    if not msg:
        return False
    bot_qq = await get_bot_qq(bot)
    if rss.user_id:
        friend_list = await get_bot_friend_list(bot)
        for user_id in rss.user_id:
            if int(user_id) not in friend_list:
                logger.error(f"QQ号[{user_id}]不是Bot[{bot_qq}]的好友 链接：[{item['link']}]")
                continue
            try:
                await bot.send_msg(
                    message_type="private", user_id=int(user_id), message=str(msg)
                )
                flag = True
            except NetworkError:
                if item.get("count") == 3:
                    logger.error(f"网络错误，消息发送失败，已达最大重试次数！链接：[{item['link']}]")
                else:
                    logger.warning(f"网络错误，消息发送失败，将重试")
            except Exception as e:
                logger.error(f"E: {e} 链接：[{item['link']}]")

    if rss.group_id:
        group_list = await get_bot_group_list(bot)
        for group_id in rss.group_id:
            if int(group_id) not in group_list:
                logger.error(f"Bot[{bot_qq}]未加入群组[{group_id}] 链接：[{item['link']}]")
                continue
            try:
                await bot.send_msg(
                    message_type="group", group_id=int(group_id), message=str(msg)
                )
                flag = True
            except NetworkError:
                if item.get("count") == 3:
                    logger.error(f"网络错误，消息发送失败，已达最大重试次数！链接：[{item['link']}]")
                else:
                    logger.warning(f"网络错误，消息发送失败，将重试")
            except Exception as e:
                logger.error(f"E: {e} 链接：[{item['link']}]")
    return flag
