import asyncio
from typing import List
from telethon import TelegramClient, events, Button
from ...config import config
from ...rss_class import Rss
from ...telegram import bot
from .telegram_command import (
    CommandInputBtnsCancel,
    CommandInputText,
    InputButton,
    wait_msg_callback,
    wait_btn_callback,
    CommandInfo,
    CommandField,
    CommandInputBtnsBool,
)


class RssCommands:
    change = CommandInfo(name="修改", command="change", description="修改订阅")
    subscribe = CommandInfo(name="订阅", command="subscribe", description="订阅")
    query = CommandInfo(name="查询", command="query", description="查询订阅")
    unsubscribe = CommandInfo(name="取消订阅", command="unsubscribe", description="取消订阅")
    help = CommandInfo(name="帮助", command="help", description="帮助")


@bot.on(events.NewMessage(pattern=config.telegram_bot_command))
async def start(event: events.newmessage.NewMessage.Event):
    btns = []
    for command in RssCommands.__dict__.values():
        if isinstance(command, CommandInfo):
            btn = Button.inline(command.name, data=command.command)
            btns.append(btn)
    # 一行显示 3 个按钮
    btns = [btns[i : i + 3] for i in range(0, len(btns), 3)]
    await event.reply(
        "选择操作:",
        buttons=btns,
    )
