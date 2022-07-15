import re

from nonebot import on_command
from nonebot.adapters.onebot.v11 import (
    GroupMessageEvent,
    Message,
    MessageEvent,
    PrivateMessageEvent,
)
from nonebot.params import CommandArg
from nonebot.rule import to_me

from ..parsing.utils import get_proxy
from ..qbittorrent_download import start_down

upload_group_file = on_command(
    "upload_file",
    aliases={"uploadfile"},
    rule=to_me(),
    priority=5,
)


@upload_group_file.handle()
async def handle_first_receive(
    event: MessageEvent, message: Message = CommandArg()
) -> None:
    if isinstance(event, PrivateMessageEvent):
        await upload_group_file.finish("请在群聊中使用该命令")
    elif isinstance(event, GroupMessageEvent):
        target = re.search(
            r"(magnet:\?xt=urn:btih:([A-F\d]{40}|[2-7A-Z]{32}))|(http.*?\.torrent)",
            str(message),
            flags=re.I,
        )
        if not target:
            await upload_group_file.finish("请输入种子链接")
            return
        await start_down(
            url=target[0],
            group_ids=[str(event.group_id)],
            name="手动上传",
            proxy=get_proxy(True),
        )
