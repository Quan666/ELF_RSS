from pathlib import Path
from typing import Any, List, Optional

from nonebot import get_driver
from nonebot.config import BaseConfig
from nonebot.log import logger
from pydantic import AnyHttpUrl, Extra

DATA_PATH = Path.cwd() / "data"
JSON_PATH = DATA_PATH / "rss.json"


class ELFConfig(BaseConfig):
    class Config:
        extra = Extra.allow

    rss_proxy: Optional[str] = None
    rsshub: AnyHttpUrl = "https://rsshub.app"  # type: ignore
    rsshub_backup: Optional[List[AnyHttpUrl]] = None
    db_cache_expire = 30
    limit = 200
    max_length: int = 1024  # 正文长度限制，防止消息太长刷屏，以及消息过长发送失败的情况

    zip_size: int = 2 * 1024
    gif_zip_size: int = 6 * 1024

    blockquote: bool = True
    black_word: Optional[List[str]] = None

    baidu_id: Optional[str] = None
    baidu_key: Optional[str] = None

    qb_username: Optional[str] = None  # qbittorrent 用户名
    qb_password: Optional[str] = None  # qbittorrent 密码
    qb_web_url: Optional[str] = None
    qb_down_path: Optional[str] = None  # qb的文件下载地址，这个地址必须是 go-cqhttp能访问到的
    down_status_msg_group: Optional[List[int]] = None
    down_status_msg_date: int = 10

    version: str = ""

    def __getattr__(self, name: str) -> Any:
        data = self.dict()
        return next(
            (v for k, v in data.items() if k.casefold() == name.casefold()), None
        )


config = ELFConfig(**get_driver().config.dict())
logger.debug(f"RSS Config loaded: {config!r}")
