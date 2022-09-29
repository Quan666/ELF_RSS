import asyncio

from telethon import events
from ...config import config
from ...rss_class import Rss
from .start import RssCommands
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

QueryCommandFields = [
    CommandField(
        description="所有订阅",
        key="query_all",
        field_type=CommandInputText,
    ),
    CommandField(
        description="当前会话",
        key="query_this",
        field_type=CommandInputText,
    ),
]


@bot.on(events.CallbackQuery(data=RssCommands.query.command))
async def change(event: events.callbackquery.CallbackQuery.Event):
    await event.delete()

    btns = [
        InputButton(field.description, data=field.key) for field in QueryCommandFields
    ]
    try:
        # 等待用户选择需要修改的字段
        field_key = await wait_btn_callback(
            bot,
            event,
            tips_text="选择需要修改的字段",
            btns=btns,
        )
        if field_key == "query_all":
            pass
        elif field_key == "query_this":
            pass

    except asyncio.TimeoutError:
        pass
    except Exception as e:
        print(e)
