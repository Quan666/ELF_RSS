import hashlib
import random
import re

import aiohttp
import emoji
from deep_translator import GoogleTranslator, DeeplTranslator, single_detection
from nonebot.log import logger

from ..config import config


async def baidu_translator(content: str) -> str:
    appid = config.baidu_id
    secret_key = config.baidu_key

    url = "https://api.fanyi.baidu.com/api/trans/vip/translate"
    salt = str(random.randint(32768, 65536))
    sign = hashlib.md5((appid + content + salt + secret_key).encode()).hexdigest()
    params = {
        "q": content,
        "from": "auto",
        "to": "zh",
        "appid": appid,
        "salt": salt,
        "sign": sign,
    }
    async with aiohttp.ClientSession() as session:
        resp = await session.get(url, params=params, timeout=aiohttp.ClientTimeout(10))
        data = await resp.json()
        try:
            content = "".join(i["dst"] + "\n" for i in data["trans_result"])
            text = "\n百度翻译：\n" + content[:-1]
            return text
        except Exception:
            error_msg = f"百度翻译失败：{data['error_msg']}"
            logger.warning(error_msg)
            raise Exception(error_msg)


async def google_translation(text: str, proxies: dict) -> str:
    # text 是处理过emoji的
    try:
        translator = GoogleTranslator(source="auto", target="zh-CN", proxies=proxies)
        return "\n谷歌翻译：\n" + str(translator.translate(re.escape(text)))
    except Exception as e:
        error_msg = "\nGoogle翻译失败：" + str(e) + "\n"
        logger.warning(error_msg)
        raise Exception(error_msg)


async def deepl_translator(text: str, proxies: dict) -> str:
    try:
        lang = None
        if config.single_detection_api_key:
            lang = single_detection(text, api_key=config.single_detection_api_key)
        return "\nDeepl翻译：\n" + DeeplTranslator(
            api_key=config.deepl_translator_api_key,
            source=lang,
            target="zh",
            use_free_api=True,
            proxies=proxies,
        ).translate(re.escape(text))
    except Exception as e:
        error_msg = "\nDeeplTranslator翻译失败：" + str(e) + "\n"
        logger.warning(error_msg)
        raise Exception(error_msg)


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

    text = emoji.demojize(content)
    text = re.sub(r":[A-Za-z_]*:", " ", text)
    try:
        # 优先级 DeeplTranslator > 百度翻译 > GoogleTranslator
        # 异常时使用 GoogleTranslator 重试
        google_translator_flag = False
        try:
            if config.deepl_translator_api_key:
                text = await deepl_translator(text=text, proxies=proxies)
            elif config.baidu_id and config.baidu_key:
                text = await baidu_translator(content=content)
            else:
                google_translator_flag = True
        except:
            google_translator_flag = True
        if google_translator_flag:
            text = await google_translation(text=text, proxies=proxies)
    except Exception as e:
        logger.error(e)
        text = str(e)

    text = text.replace("\\", "")
    return text
