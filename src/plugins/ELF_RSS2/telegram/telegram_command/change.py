import asyncio
from typing import Any, Dict, List, Union

from nonebot.log import logger
from telethon import events

from ...rss_class import Rss
from ...telegram import bot
from .start import RssCommands
from .telegram_command import (
    CommandField,
    CommandInputBtnsBool,
    CommandInputBtnsCancel,
    CommandInputListStr,
    CommandInputText,
    InputButton,
    wait_btn_callback,
)

attribute_dict = {
    "name": {
        "zh": "订阅名称",
        "description": "",
    },
    "url": {
        "zh": "订阅地址",
        "description": "",
    },
    "user_id": {
        "zh": "订阅Q号",
        "description": "",
    },
    "group_id": {
        "zh": "订阅Q群",
        "description": "",
    },
    "guild_channel_id": {
        "zh": "订阅QQ频道",
        "description": "",
    },
    "time": {
        "zh": "更新频率",
        "description": "",
    },
    "img_proxy": {
        "zh": "代理",
        "description": "",
    },
    "translation": {
        "zh": "翻译",
        "description": "",
    },
    "only_title": {
        "zh": "仅标题",
        "description": "",
    },
    "only_pic": {
        "zh": "仅图片",
        "description": "",
    },
    "only_has_pic": {
        "zh": "仅存在图片",
        "description": "",
    },
    "download_pic": {
        "zh": "下载图片",
        "description": "",
    },
    "is_open_upload_group": {
        "zh": "上传到Q群",
        "description": "",
    },
    "down_torrent": {
        "zh": "下载种子",
        "description": "",
    },
    "down_torrent_keyword": {
        "zh": "下载种子关键词",
        "description": "",
    },
    "black_keyword": {
        "zh": "黑名单关键词",
        "description": "",
    },
    "duplicate_filter_mode": {
        "zh": "去重模式",
        "description": "",
    },
    "max_image_number": {
        "zh": "限制图片数量",
        "description": "",
    },
    "stop": {
        "zh": "暂停",
        "description": "",
    },
    "pikpak_offline": {
        "zh": "PikPak离线",
        "description": "",
    },
    "pikpak_path_key": {
        "zh": "PikPak离线路径正则",
        "description": "",
    },
}


def get_change_command_fields(
    rss: Rss, event: events.CallbackQuery.Event
) -> List[CommandField]:
    """获取修改订阅的字段"""
    fields = []
    # 获取rss的所有字段
    for key, value in rss.__dict__.items():
        field_info = attribute_dict.get(
            key,
            {
                "zh": key,
                "description": "",
            },
        )
        if isinstance(value, bool):
            fields.append(
                CommandField(
                    key=key,
                    name=field_info["zh"],
                    description=field_info["description"],
                    command_input=CommandInputBtnsBool(
                        bot=bot,
                        event=event,
                        tips_text=f"{field_info['zh']} 当前值为\n{value}",
                    ),
                )
            )
        elif isinstance(value, list):
            fields.append(
                CommandField(
                    key=key,
                    name=field_info["zh"],
                    description=field_info["description"],
                    command_input=CommandInputListStr(
                        bot=bot,
                        event=event,
                        tips_text=f"{field_info['zh']}",
                        old_list=value,
                    ),
                )
            )
        else:
            fields.append(
                CommandField(
                    key=key,
                    name=field_info["zh"],
                    description=field_info["description"],
                    command_input=CommandInputText(
                        bot=bot,
                        event=event,
                        tips_text=f"{field_info['zh']} 当前值为:\n{value}",
                    ),
                )
            )
    fields.append(
        CommandField(
            key="cancel",
            name="取消",
            description="取消修改",
            command_input=CommandInputBtnsCancel(
                bot=bot,
                event=event,
                tips_text="取消修改",
            ),
        )
    )
    return fields


def change_rss_field_value(
    rss: Rss, field_key: str, value: Union[str, bool, List[str], Dict[str, str], Any]
) -> bool:
    """修改订阅字段"""
    if type(value) == type(getattr(rss, field_key)):
        setattr(rss, field_key, value)
        return True
    return False


@bot.on(events.CallbackQuery(data=RssCommands.change.command))  # type: ignore
async def change(event: events.CallbackQuery.Event) -> None:
    await event.delete()

    try:

        # 选择需要修改的订阅
        # 获取订阅列表
        rss_list = Rss.read_rss()
        btns = [InputButton(rss.name, data=rss.name) for rss in rss_list]

        # 等待用户选择需要修改的订阅
        rss_name = await wait_btn_callback(
            bot,
            event,
            tips_text="选择需要修改的订阅",
            btns=btns,
        )
        rss = Rss.get_one_by_name(rss_name)
        if not rss:
            return

        while True:
            tips_text = f"{rss}\n选择需要修改的属性:"
            fields = get_change_command_fields(rss, event)
            # 需要修改的订阅字段
            btns = [InputButton(field.name, data=field.key) for field in fields]
            # 等待用户选择需要修改的字段
            field_key = await wait_btn_callback(
                bot,
                event,
                tips_text=tips_text,
                btns=btns,
            )
            if field_key == "cancel":
                return

            # 发送需要修改的字段的值
            field = next(field for field in fields if field.key == field_key)
            result = await field.command_input.input()
            if change_rss_field_value(rss, field_key, result):
                if field_key == "name":
                    rss.upsert(rss_name)
                else:
                    rss.upsert()

    except asyncio.TimeoutError:
        logger.warning("超时，已取消")
    except Exception as e:
        import traceback

        traceback.print_exc()
        logger.error(e)
