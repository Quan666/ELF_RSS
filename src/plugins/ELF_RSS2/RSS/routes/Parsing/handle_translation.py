import re
import random
import httpx
import hashlib
import emoji

from translate import Translator

from ....config import config
from nonebot import logger


# 翻译
async def handle_translation(content: str) -> str:
    translator = Translator(to_lang="zh", from_lang="autodetect")
    appid = config.baidu_id
    secret_key = config.baidu_key
    text = emoji.demojize(content)
    text = re.sub(r":[A-Za-z_]*:", " ", text)
    try:
        if appid and secret_key:
            url = f"https://api.fanyi.baidu.com/api/trans/vip/translate"
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
            async with httpx.AsyncClient(proxies={}) as client:
                r = await client.get(url, params=params, timeout=10)
            try:
                i = 0
                content = ""
                while i < len(r.json()["trans_result"]):
                    content += r.json()["trans_result"][i]["dst"] + "\n"
                    i += 1
                text = "\n百度翻译：\n" + content[:-1]
            except Exception as e:
                logger.warning("使用百度翻译错误：" + str(r.json()["error_msg"]) + "，开始尝试使用谷歌翻译")
                text = "\n谷歌翻译：\n" + str(translator.translate(re.escape(text)))
        else:
            text = "\n谷歌翻译：\n" + str(translator.translate(re.escape(text)))
        text = re.sub(r"\\", "", text)
    except Exception as e:
        text = "\n翻译失败！" + str(e) + "\n"
    return text
