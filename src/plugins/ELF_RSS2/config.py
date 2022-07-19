from pathlib import Path
from typing import List, Optional

from nonebot import get_driver
from nonebot.config import BaseConfig
from nonebot.log import logger
from pydantic import AnyHttpUrl

DATA_PATH = Path.cwd() / "data"
JSON_PATH = DATA_PATH / "rss.json"


class ELFConfig(BaseConfig):
    class Config:
        extra = "allow"

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

    pikpak_username: Optional[str] = None  # pikpak 用户名
    pikpak_password: Optional[str] = None  # pikpak 密码
    pikpak_download_path: str = (
        ""  # pikpak 离线保存的目录, 默认是根目录，示例: ELF_RSS/Downloads ,目录不存在会自动创建, 不能/结尾
    )


config = ELFConfig(**get_driver().config.dict())
logger.debug(f"RSS Config loaded: {config!r}")
