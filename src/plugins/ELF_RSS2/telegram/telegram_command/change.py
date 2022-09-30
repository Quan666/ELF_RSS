import asyncio
from nonebot.log import logger

from telethon import events

from ...telegram import bot
from .start import RssCommands
from .telegram_command import (
    CommandField,
    CommandInputBtnsBool,
    CommandInputBtnsCancel,
    CommandInputText,
    InputButton,
    wait_btn_callback,
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


@bot.on(events.CallbackQuery(data=RssCommands.change.command))  # type: ignore
async def change(event: events.CallbackQuery.Event) -> None:
    await event.delete()
    # 获取message
    # message = await event.get_message
    print(event)

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
        logger.warning("超时，已取消")
    except Exception as e:
        logger.error(e)
