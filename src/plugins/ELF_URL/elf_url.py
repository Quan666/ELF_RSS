import json

from httpx import AsyncClient
from nonebot import on_command
from nonebot.adapters.cqhttp import Bot, Event
from nonebot.rule import to_me

url = on_command("短链", rule=to_me(), priority=5)


@url.handle()
async def handle_first_receive(bot: Bot, event: Event, state: dict):
    args = str(event.message).strip()  # 首次发送命令时跟随的参数，例：/天气 上海，则args为上海
    if args:
        state["url"] = args  # 如果用户发送了参数则直接赋值


@url.got("url", prompt="输入你想要缩短的链接")
async def handle_city(bot: Bot, event: Event, state: dict):
    link = state["url"]
    # if link not in ["上海", "北京"]:
    #     await url.reject("你想查询的城市暂不支持，请重新输入！")
    uri = await get_uri_of_url(link)
    await url.finish(uri)


async def get_uri_of_url(url: str) -> str:
    www = 'https://ii1.fun/url/insert'
    data = {"url": url}
    headers = {'Content-Type': 'application/json'}
    try:
        async with AsyncClient(headers=headers) as client:
            data_json = await client.get(www,  data=json.dumps(data)).json()
        return data_json['data']['shortUrl']
    except:
        return '获取短链接出错'
