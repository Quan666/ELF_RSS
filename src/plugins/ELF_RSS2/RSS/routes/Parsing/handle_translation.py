import emoji
import re
import unicodedata

from google_trans_new import google_translator

from ....RSS import translation_baidu
from ....config import config


# 翻译
async def handle_translation(content: str) -> str:
    translator = google_translator()
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
            text = "\n翻译：\n" + str(translator.translate(re.escape(text), lang_tgt="zh"))
        text = re.sub(r"\\", "", text)
        text = re.sub(r"百度翻译", "\n", text)
    except Exception as e:
        text = "\n翻译失败！" + str(e) + "\n"
    return text
