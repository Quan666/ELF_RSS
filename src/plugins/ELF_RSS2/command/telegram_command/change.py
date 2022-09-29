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

ChangeCommandFields = [
    CommandField(
        description="订阅名称",
        key="name",
        field_type=CommandInputText,
    ),
    CommandField(
        description="订阅地址",
        key="url",
        field_type=CommandInputText,
    ),
    CommandField(
        description="是否启用",
        key="enable",
        field_type=CommandInputBtnsBool,
    ),
    CommandField(
        description="取消",
        key="cancel",
        field_type=CommandInputBtnsCancel,
    ),
]


@bot.on(events.CallbackQuery(data=RssCommands.change.command))
async def change(event: events.callbackquery.CallbackQuery.Event):
    await event.delete()

    # 发送需要修改的订阅字段
    btns = [
        InputButton(field.description, data=field.key) for field in ChangeCommandFields
    ]
    try:
        while True:
            # 等待用户选择需要修改的字段
            field_key = await wait_btn_callback(
                bot,
                event,
                tips_text="选择需要修改的字段",
                btns=btns,
            )
            if field_key == "cancel":
                return

            # 发送需要修改的字段的值
            field = next(
                field for field in ChangeCommandFields if field.key == field_key
            )
            result = await field.field_type(
                bot=bot, event=event, tips_text=field.description
            ).input()
            print(result)
    except asyncio.TimeoutError:
        pass
    except Exception as e:
        print(e)
