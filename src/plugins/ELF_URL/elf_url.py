import json
from urllib.parse import quote

import httpx
from httpx import AsyncClient
from nonebot import on_command, logger
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
    uri = await get_uri_of_url(link)
    await url.finish(uri)


async def get_uri_of_url(url: str) -> str:
    www = 'https://oy.mk/api/insert'
    # data = {"url": url}
    # headers = {'Content-Type': 'application/json'}
    async with httpx.AsyncClient(proxies={}) as client:
        try:
            url = quote(url, 'utf-8')
            # res = await client.post(www, headers=headers, data=json.dumps(data))
            res = await client.get(f'{www}?url={url}')
            res = res.json()
            if res['code'] != 200:
                raise Exception('获取短链错误')
            return res['data']['url']
        except Exception as e:
            logger.error(e)
            return f'获取短链出错：{e}'
