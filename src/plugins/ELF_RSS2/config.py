import os
from typing import List, Any

from nonebot import get_driver, logger
from nonebot.config import BaseConfig
from pydantic import AnyHttpUrl, Extra


class ELFConfig(BaseConfig):
    class Config:
        extra = Extra.allow

    rss_proxy: str = ''
    rsshub: AnyHttpUrl = 'https://rsshub.app'
    rsshub_backup: List[AnyHttpUrl] = []
    delcache: int = 3
    limt = 50

    zip_size: int = 3 * 1024

    blockquote: bool = True
    showblockword: bool = True
    blockword: List[str] = ["互动抽奖", "微博抽奖平台"]

    usebaidu: bool = False
    baiduid: str = ''
    baidukey: str = ''

    islinux: bool = (os.name != 'nt')

    close_pixiv_cat: bool = False

    is_open_auto_down_torrent: bool = False
    qb_web_url: str = 'http://127.0.0.1:8081'
    down_status_msg_grou: List[int] = []
    down_status_msg_date: int = 10
    local_ip: str = ''  # 还没写完

    version: str = "v2.1.7"

    def __getattr__(self, name: str) -> Any:
        data = self.dict()
        for k, v in data.items():
            if k.casefold() == name.casefold():
                return v
        return None


config = ELFConfig(get_driver().config.dict())
logger.debug(f'RSS Config loaded: {config!r}')
