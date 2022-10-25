import asyncio

from telethon import events
from .permission import handle_permission
from ...telegram import bot
from .start import RssCommands
from .telegram_command import CommandInputText
from ...rss_class import Rss




@bot.on(events.CallbackQuery(data=RssCommands.subscribe.command, func=lambda e: handle_permission(e)))  # type: ignore
async def change(event: events.CallbackQuery.Event) -> None:
    await event.delete()
    try:
        rss_name = CommandInputText(bot,event,"请输入订阅名称").input()
        rss_url = CommandInputText(bot,event,"请输入订阅地址").input()
        rss = Rss(rss_name,rss_url)
        if _ := Rss.get_one_by_name(rss_name):
            await event.respond(f"订阅名称已存在")
            return
        rss.telegram_channel_id.append(event.chat_id)
        # TODO 保存，添加定时任务

    except asyncio.TimeoutError:
        pass
    except Exception as e:
        print(e)
