from telethon import Button, events

from ...config import config
from ...telegram import bot
from .telegram_command import CommandInfo, buttons_layout


class RssCommands:
    subscribe = CommandInfo(name="订阅", command="subscribe", description="订阅")
    change = CommandInfo(name="修改", command="change", description="修改订阅")
    query = CommandInfo(name="查询", command="query", description="查询订阅")
    unsubscribe = CommandInfo(name="取消订阅", command="unsubscribe", description="取消订阅")
    help = CommandInfo(name="帮助", command="help", description="帮助")


@bot.on(events.NewMessage(pattern=config.telegram_bot_command, from_users=config.telegram_admin_ids))  # type: ignore
async def start(event: events.NewMessage.Event) -> None:
    btns = []
    for command in RssCommands.__dict__.values():
        if isinstance(command, CommandInfo):
            btn = Button.inline(command.name, data=command.command)
            btns.append(btn)
    await event.reply(
        "选择操作:",
        buttons=buttons_layout(btns),
    )
