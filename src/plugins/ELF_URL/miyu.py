import json

from httpx import AsyncClient
from nonebot import on_command
from nonebot.adapters.cqhttp import Bot, Event
from nonebot.rule import to_me

MIYU = on_command("密语", rule=to_me(), priority=5)


@MIYU.handle()
async def handle_first_receive(bot: Bot, event: Event, state: dict):
    args = str(event.get_message()).strip()  # 首次发送命令时跟随的参数，例：/天气 上海，则args为上海
    if args:
        state["MIYU"] = args  # 如果用户发送了参数则直接赋值


@MIYU.got("MIYU", prompt="发送“密语”信息，及密码，空格分割")
async def handle_city(bot: Bot, event: Event, state: dict):
    txt = state["MIYU"]
    miyu_list = txt.split(" ")
    if len(miyu_list) < 2:
        await MIYU.reject("发送“密语”信息，及密码，空格分割")

    re = await get_miyu(miyu_list[0], miyu_list[1])
    await MIYU.finish(re)


async def get_miyu(message: str, passwd: str) -> str:
    api = "https://ii1.fun/cipher/insert"
    data = {"message": message, "passwd": passwd}
    headers = {"Content-Type": "application/json"}
    async with AsyncClient(proxies={}, headers=headers) as client:
        data_json = await client.post(api, data=json.dumps(data))
        data_json = data_json.json()
    return "" + data_json["data"]["shortUrl"]
