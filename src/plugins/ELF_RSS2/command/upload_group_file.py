import re

from nonebot import on_command
from nonebot.adapters.onebot.v11 import (
    Event,
    GroupMessageEvent,
    Message,
    PrivateMessageEvent,
)
from nonebot.params import CommandArg
from nonebot.rule import to_me

from ..qbittorrent_download import start_down
from ..parsing.utils import get_proxy

upload_group_file = on_command(
    "upload_file", aliases={"uploadfile"}, rule=to_me(), priority=5,
)


@upload_group_file.handle()
async def handle_first_receive(event: Event, message: Message = CommandArg()) -> None:
    if isinstance(event, PrivateMessageEvent):
        await upload_group_file.finish("请在群聊中使用该命令")
    elif isinstance(event, GroupMessageEvent):
        target = re.search(
            "(magnet:\?xt=urn:btih:[a-fA-F0-9]{40})|(http.*?\.torrent)", str(message),
        )
        if not target:
            await upload_group_file.finish("请输入种子链接")
        await start_down(
            url=target[0],
            group_ids=[event.group_id],
            name="手动上传",
            proxy=get_proxy(True),
        )
