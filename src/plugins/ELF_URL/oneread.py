import json

from httpx import AsyncClient
from nonebot import on_command
from nonebot.adapters.cqhttp import Bot, Event
from nonebot.rule import to_me

oneread = on_command(
    '阅后即焚', aliases={'阅后即焚', 'yhjf'}, rule=to_me(), priority=5)


@oneread.handle()
async def handle_first_receive(bot: Bot, event: Event, state: dict):
    args = str(event.message).strip()  # 首次发送命令时跟随的参数，例：/天气 上海，则args为上海
    if args:
        state["oneread"] = args  # 如果用户发送了参数则直接赋值


@oneread.got("oneread", prompt="发送“阅后即焚”信息")
async def handle_city(bot: Bot, event: Event, state: dict):
    txt = state["oneread"]
    re = await get_oneread(txt)
    await oneread.finish(re)


async def get_oneread(oneread: str) -> str:
    www = 'https://ii1.fun/oneread/insert'
    data = {"message": oneread}
    headers = {'Content-Type': 'application/json'}
    async with AsyncClient(proxies={}, headers=headers) as client:
        data_json = await client.post(www, headers=headers, data=json.dumps(data))
        data_json = data_json.json()
    return data_json['data']['shortUrl']
