from nonebot.adapters.onebot.v11.bot import Bot, _check_nickname
from nonebot.adapters.onebot.v11.event import Event
from nonebot.adapters.onebot.v11.message import MessageSegment
from nonebot.message import handle_event
from nonebot_plugin_guild_patch import GuildMessageEvent


def _check_at_me(bot: Bot, event: GuildMessageEvent) -> None:
    """
    :说明:
      检查频道消息开头或结尾是否存在 @机器人，去除并赋值 ``event.to_me``
    :参数:
      * ``bot: Bot``: Bot 对象
      * ``event: GuildMessageEvent``: GuildMessageEvent 对象
    """

    # ensure message not empty
    if not event.message:
        event.message.append(MessageSegment.text(""))

    if event.message_type == "private":
        event.to_me = True
    else:

        def _is_at_me_seg(segment: MessageSegment) -> bool:
            return segment.type == "at" and str(segment.data.get("qq", "")) == str(
                event.self_tiny_id
            )

        # check the first segment
        if _is_at_me_seg(event.message[0]):
            event.to_me = True
            event.message.pop(0)
            if event.message and event.message[0].type == "text":
                event.message[0].data["text"] = event.message[0].data["text"].lstrip()
                if not event.message[0].data["text"]:
                    del event.message[0]
            if event.message and _is_at_me_seg(event.message[0]):
                event.message.pop(0)
                if event.message and event.message[0].type == "text":
                    event.message[0].data["text"] = (
                        event.message[0].data["text"].lstrip()
                    )
                    if not event.message[0].data["text"]:
                        del event.message[0]

        if not event.to_me:
            # check the last segment
            i = -1
            last_msg_seg = event.message[i]
            if (
                last_msg_seg.type == "text"
                and not last_msg_seg.data["text"].strip()
                and len(event.message) >= 2
            ):
                i -= 1
                last_msg_seg = event.message[i]

            if _is_at_me_seg(last_msg_seg):
                event.to_me = True
                del event.message[i:]

        if not event.message:
            event.message.append(MessageSegment.text(""))


original_handle_event = Bot.handle_event


async def patched_handle_event(self: Bot, event: Event) -> None:
    if not isinstance(event, GuildMessageEvent):
        await original_handle_event(self, event)
    else:
        _check_at_me(self, event)
        _check_nickname(self, event)

        await handle_event(self, event)


Bot.handle_event = patched_handle_event  # type: ignore
