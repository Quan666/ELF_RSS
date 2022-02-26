import re
import unicodedata

import emoji
from googletrans import Translator
from httpcore import SyncHTTPProxy

from ....config import config
from ....RSS import translation_baidu


# 翻译
async def handle_translation(content: str) -> str:
    if config.rss_proxy and len(config.rss_proxy.split(":")) == 2:
        proxy = SyncHTTPProxy(
            (
                b"http",
                bytes(config.rss_proxy.split(":")[0], encoding="utf-8"),
                int(config.rss_proxy.split(":")[1]),
                b"",
            )
        )
        translator = Translator(proxies={"http": proxy, "https": proxy})
    translator = Translator()
    try:
        text = emoji.demojize(content)
        text = re.sub(r":[A-Za-z_]*:", " ", text)
        if config.baidu_id and config.baidu_key:
            content = re.sub(r"\n", "百度翻译 ", content)
            content = unicodedata.normalize("NFC", content)
            text = emoji.demojize(content)
            text = re.sub(r":[A-Za-z_]*:", " ", text)
            text = "\n翻译(BaiduAPI)：\n" + str(
                translation_baidu.baidu_translate(re.escape(text))
            )
        else:
            text = "\n翻译：\n" + str(translator.translate(re.escape(text), dest="zh-cn"))
        text = re.sub(r"\\", "", text)
        text = re.sub(r"百度翻译", "\n", text)
    except Exception as e:
        text = "\n翻译失败！" + str(e) + "\n"
    return text
