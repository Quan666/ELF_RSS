import json

from httpx import AsyncClient
from nonebot import on_command
from nonebot.adapters.cqhttp import Bot, Event
from nonebot.rule import to_me

ONE_READ = on_command("阅后即焚", aliases={"阅后即焚", "yhjf"}, rule=to_me(), priority=5)


@ONE_READ.handle()
async def handle_first_receive(bot: Bot, event: Event, state: dict):
    args = str(event.get_message()).strip()  # 首次发送命令时跟随的参数，例：/天气 上海，则args为上海
    if args:
        state["ONE_READ"] = args  # 如果用户发送了参数则直接赋值


@ONE_READ.got("ONE_READ", prompt="发送“阅后即焚”信息")
async def handle_city(bot: Bot, event: Event, state: dict):
    txt = state["ONE_READ"]
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
