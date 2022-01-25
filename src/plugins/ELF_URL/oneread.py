import json

from httpx import AsyncClient
from nonebot import on_command
from nonebot.typing import T_State
from nonebot.params import CommandArg, State
from nonebot.adapters.onebot.v11 import Bot, Event, Message
from nonebot.rule import to_me

ONE_READ = on_command("阅后即焚", aliases={"阅后即焚", "yhjf"}, rule=to_me(), priority=5)


@ONE_READ.handle()
async def handle_first_receive(
    message: Message = CommandArg(), state: T_State = State()
):
    args = str(message).strip()
    if args:
        state["ONE_READ"] = args


@ONE_READ.got("ONE_READ", prompt="发送“阅后即焚”信息")
async def handle_city(state: T_State = State()):
    txt = str(state["ONE_READ"])
    re = await get_once_read(txt)
    await ONE_READ.finish(re)


async def get_once_read(once_read: str) -> str:
    api = "https://ii1.fun/oneread/insert"
    data = {"message": once_read}
    headers = {"Content-Type": "application/json"}
    async with AsyncClient(proxies={}, headers=headers) as client:
        data_json = await client.post(api, headers=headers, data=json.dumps(data))
        data_json = data_json.json()
    return data_json["data"]["shortUrl"]
