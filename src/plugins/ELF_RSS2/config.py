import os
from typing import List

from nonebot import get_driver
from nonebot.config import Config
from pydantic import AnyHttpUrl, Extra


class ELFConfig(Config):

    class Config:
        extra = Extra.allow

    RSS_PROXY: str = ''
    RSSHUB: AnyHttpUrl = 'https://rsshub.app'
    RSSHUB_BACKUP: List[AnyHttpUrl] = []
    DELCACHE: int = 3
    LIMT = 50

    ZIP_SIZE: int = 3 * 1024

    blockquote: bool = True
    showBlockword: bool = True
    Blockword: List[str] = ["互动抽奖", "微博抽奖平台"]

    UseBaidu: bool = False
    BaiduID: str = ''
    BaiduKEY: str = ''

    IsLinux: bool = (os.name != 'nt')

    is_open_auto_down_torrent: bool = False
    qb_web_url: str = 'http://127.0.0.1:8081'
    down_status_msg_grou: List[int] = []
    down_status_msg_date: int = 10

    VERSION: str = "v2.1.6"


config = ELFConfig.parse_obj(get_driver().config.dict())
