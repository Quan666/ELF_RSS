import hashlib
import random
import re

import aiohttp
import emoji
from deep_translator import GoogleTranslator
from nonebot.log import logger

from ..config import config


# 翻译
async def handle_translation(content: str) -> str:
    proxies = (
        {
            "https": config.rss_proxy,
            "http": config.rss_proxy,
        }
        if config.rss_proxy
        else None
    )
    translator = GoogleTranslator(source="auto", target="zh-CN", proxies=proxies)
    appid = config.baidu_id
    secret_key = config.baidu_key
    text = emoji.demojize(content)
    text = re.sub(r":[A-Za-z_]*:", " ", text)
    try:
        if appid and secret_key:
            url = "https://api.fanyi.baidu.com/api/trans/vip/translate"
            salt = str(random.randint(32768, 65536))
            sign = hashlib.md5(
                (appid + content + salt + secret_key).encode()
            ).hexdigest()
            params = {
                "q": content,
                "from": "auto",
                "to": "zh",
                "appid": appid,
                "salt": salt,
                "sign": sign,
            }
            async with aiohttp.ClientSession() as session:
                resp = await session.get(
                    url, params=params, timeout=aiohttp.ClientTimeout(10)
                )
                data = await resp.json()
                try:
                    content = "".join(i["dst"] + "\n" for i in data["trans_result"])
                    text = "\n百度翻译：\n" + content[:-1]
                except Exception:
                    logger.warning(f"使用百度翻译错误：{data['error_msg']}，开始尝试使用谷歌翻译")
                    text = "\n谷歌翻译：\n" + str(translator.translate(re.escape(text)))
        else:
            text = "\n谷歌翻译：\n" + str(translator.translate(re.escape(text)))
        text = text.replace("\\", "")
    except Exception as e:
        text = "\n翻译失败！" + str(e) + "\n"
    return text
