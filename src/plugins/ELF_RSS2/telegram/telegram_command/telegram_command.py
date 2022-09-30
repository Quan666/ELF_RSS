import asyncio
from typing import Any, List, Optional, Union

from telethon import Button, TelegramClient, events

from ...rss_class import Rss


class InputButton:
    def __init__(self, text: str, data: str):
        self.text = text
        self.data = data


async def wait_msg_callback(
    bot: TelegramClient,
    event: events.CallbackQuery.Event,
    msg: str,
    timeout: float = 60,
    placeholder: Optional[str] = None,
    remove_text: bool = False,
) -> str:
    # 等待用户发送消息
    # 需要用户输入的信息
    async with bot.conversation(
        await event.get_chat(), timeout=timeout, exclusive=False
    ) as conv:
        # @用户
        if event.sender.username:
            msg += f" \n@{event.sender.username}"
        else:
            # 文字提及用户
            msg += f" [@{event.sender.first_name}](tg://user?id={event.sender_id})"

        ans = await conv.send_message(
            msg,
            buttons=Button.force_reply(
                single_use=True,
                selective=True,
                placeholder=placeholder,
            ),
        )
        cancel_btn = await conv.send_message(
            "取消输入", buttons=[Button.inline("取消", "cancel")]
        )
        try:
            while True:
                wait_event = [
                    conv.get_response(timeout=timeout),
                    conv.wait_event(
                        events.CallbackQuery(
                            func=lambda e: e.sender_id == event.sender_id
                        ),
                        timeout=timeout,
                    ),
                ]
                done, pending = await asyncio.wait(
                    wait_event, return_when=asyncio.FIRST_COMPLETED
                )
                for task in pending:
                    task.cancel()
                e = done.pop().result()
                if isinstance(e, events.CallbackQuery.Event):
                    if e.data.decode() == "cancel":
                        await e.delete()
                        await cancel_btn.delete()
                        await ans.delete()
                        raise asyncio.TimeoutError
                if e.sender_id == event.sender_id:
                    return str(e.message)
        finally:
            if remove_text:
                await ans.delete()


async def wait_btn_callback(
    bot: TelegramClient,
    event: events.CallbackQuery.Event,
    tips_text: str,
    btns: List[InputButton],
    remove_btn: bool = True,
    timeout: float = 60,
    size: int = 3,
) -> str:
    datas = [btn.data for btn in btns]
    # 一行size个按钮，从 self.btns 里取
    buttons = [
        list(map(lambda b: Button.inline(b.text, b.data), btns[i : i + size]))
        for i in range(0, len(btns), size)
    ]

    # 等待用户点击按钮
    async with bot.conversation(
        await event.get_chat(), timeout=timeout, exclusive=False
    ) as conv:
        ans = await conv.send_message(tips_text, buttons=buttons)
        try:
            while True:
                # 等待用户点击按钮
                res = await conv.wait_event(
                    events.CallbackQuery(func=lambda e: e.sender_id == event.sender_id),
                    timeout=timeout,
                )
                # bytes 转字符串
                data: str = res.data.decode()
                if data in datas:
                    return data
        finally:
            if remove_btn:
                # 删除按钮
                await ans.delete()


from abc import ABCMeta, abstractmethod


class CommandInputBase(metaclass=ABCMeta):
    def __init__(
        self,
        bot: TelegramClient,
        event: events.CallbackQuery.Event,
        tips_text: str,
    ):
        self.bot = bot
        self.event = event
        self.tips_text = tips_text

    @abstractmethod
    async def input(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError


class CommandInfo:
    def __init__(self, name: str, command: str, description: str):
        self.name = name
        self.command = command
        self.description = description


class CommandField:
    def __init__(
        self,
        key: str,
        name: str,
        description: str,
        command_input: Any,
        value: Any = None,
    ):
        self.key = key
        self.name = name
        self.description = description
        self.command_input = command_input
        self.value = value


class CommandInputText(CommandInputBase):
    def __init__(
        self,
        bot: TelegramClient,
        event: events.CallbackQuery.Event,
        tips_text: str,
    ):
        super().__init__(bot, event, tips_text)

    async def input(
        self,
        placeholder: Optional[str] = None,
        timeout: float = 60,
    ) -> Optional[str]:
        try:
            return await wait_msg_callback(
                self.bot,
                self.event,
                self.tips_text,
                timeout=timeout,
                placeholder=placeholder,
            )

        except asyncio.TimeoutError:
            await self.event.answer("超时，已取消")
            return None


class CommandInputBtns(CommandInputBase):
    def __init__(
        self,
        bot: TelegramClient,
        event: events.CallbackQuery.Event,
        tips_text: str,
        btns: List[InputButton],
    ):
        super().__init__(bot, event, tips_text)
        self.btns = btns

    async def input(
        self, timeout: float = 60, remove_btn: bool = True
    ) -> Union[Optional[str], Any]:

        try:
            return await wait_btn_callback(
                self.bot,
                self.event,
                tips_text=self.tips_text,
                btns=self.btns,
                remove_btn=remove_btn,
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            await self.event.answer("超时，已取消")
            return None


class CommandInputBtnsBool(CommandInputBtns):
    def __init__(
        self,
        bot: TelegramClient,
        event: events.CallbackQuery.Event,
        tips_text: str,
        btn_yes_text: str = "True",
        btn_no_text: str = "False",
    ):
        super().__init__(
            bot,
            event,
            tips_text,
            [InputButton(btn_yes_text, "True"), InputButton(btn_no_text, "False")],
        )

    async def input(self, timeout: float = 60, remove_btn: bool = True) -> bool:
        return (await super().input(timeout=timeout, remove_btn=remove_btn)) == "True"


class CommandInputBtnsCancel(CommandInputBtns):
    def __init__(
        self,
        bot: TelegramClient,
        event: events.CallbackQuery.Event,
        tips_text: str,
    ):
        super().__init__(
            bot,
            event,
            tips_text,
            [InputButton("取消", "cancel")],
        )

    async def input(self, timeout: float = 60, remove_btn: bool = True) -> bool:
        return (await super().input(timeout=timeout, remove_btn=remove_btn)) == "cancel"


class CommandInputListStr(CommandInputBtns):
    def __init__(
        self,
        bot: TelegramClient,
        event: events.CallbackQuery.Event,
        tips_text: str,
        old_list: List[str],
    ):
        self.old_list = old_list
        self.tips_text = tips_text + "\n当前列表："
        self.prefix = f"{event.id}_input_btns_old_"
        self.reflush()
        super().__init__(
            bot,
            event,
            tips_text,
            btns=self.btns,
        )

    def reflush(self) -> None:
        self.btns = [
            InputButton(f"{i + 1}. {item}", f"{self.prefix}{i}")
            for i, item in enumerate(self.old_list)
        ]
        self.btns.extend(
            [
                InputButton("新增", f"{self.prefix}add"),
                InputButton("完成", f"{self.prefix}cancel"),
            ]
        )

    def __add_item(self, item: str) -> None:
        self.old_list.append(item)
        self.reflush()

    def __del_item(self, index: int) -> None:
        self.old_list.pop(index)
        self.reflush()

    async def input(self, timeout: float = 60, remove_btn: bool = True) -> List[str]:
        while True:
            data = await super().input(timeout=timeout, remove_btn=remove_btn)
            if not data or data == f"{self.prefix}cancel":
                return self.old_list
            elif data == f"{self.prefix}add":
                in_text = await CommandInputText(self.bot, self.event, "请输入：").input()
                if in_text:
                    self.__add_item(in_text)
            elif data.startswith(self.prefix):
                index = int(data[len(self.prefix) :])
                confirm = await CommandInputBtnsBool(
                    self.bot, self.event, f"{self.old_list[index]}\n确认删除？"
                ).input()
                if confirm:
                    self.__del_item(index)
