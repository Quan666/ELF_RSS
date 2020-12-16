import json

from nonebot import on_command
from nonebot.rule import to_me
from nonebot.adapters.cqhttp import Bot, Event
import requests

miyu = on_command("密语", rule=to_me(), priority=5)


@miyu.handle()
async def handle_first_receive(bot: Bot, event: Event, state: dict):
    args = str(event.message).strip()  # 首次发送命令时跟随的参数，例：/天气 上海，则args为上海
    if args:
        state["miyu"] = args  # 如果用户发送了参数则直接赋值


@miyu.got("miyu", prompt="发送“密语”信息，及密码，空格分割")
async def handle_city(bot: Bot, event: Event, state: dict):
    txt = state["miyu"]
    miyu_list = txt.split(' ')
    if len(miyu_list)<2:
        await miyu.reject("发送“密语”信息，及密码，空格分割")

    re = await get_miyu(miyu_list[0],miyu_list[1])
    await miyu.finish(re)


async def get_miyu(message: str,passwd:str) -> str:
    www = 'https://ii1.fun/cipher/insert'
    data = {"message": message,"passwd":passwd}
    headers = {'Content-Type': 'application/json'}
    data_json = requests.get(www, headers=headers, data=json.dumps(data)).json()
    return ''+data_json['data']['shortUrl']