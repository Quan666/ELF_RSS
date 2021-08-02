import nonebot

from nonebot import logger
from nonebot.adapters.cqhttp import NetworkError

from ....RSS import rss_class


# 发送消息
async def send_msg(rss: rss_class.Rss, msg: str, item: dict) -> bool:
    (bot,) = nonebot.get_bots().values()
    flag = False
    if not msg:
        return False
    if rss.user_id:
        for user_id in rss.user_id:
            try:
                await bot.send_msg(
                    message_type="private", user_id=user_id, message=str(msg)
                )
                flag = True
            except NetworkError:
                logger.error(f"网络错误,消息发送失败,将重试 链接：[{item['link']}]")
            except Exception as e:
                logger.error(f"QQ号[{user_id}]不合法或者不是好友 E: {e}")

    if rss.group_id:
        for group_id in rss.group_id:
            try:
                await bot.send_msg(
                    message_type="group", group_id=group_id, message=str(msg)
                )
                flag = True
            except NetworkError:
                logger.error(f"网络错误,消息发送失败,将重试 链接：[{item['link']}]")
            except Exception as e:
                logger.error(f"群号[{group_id}]不合法或者未加群 E: {e}")
    return flag
