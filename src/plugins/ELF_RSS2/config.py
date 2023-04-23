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
    rsshub_backup: List[AnyHttpUrl] = []
    db_cache_expire: int = 30
    limit: int = 200
    max_length: int = 1024  # 正文长度限制，防止消息太长刷屏，以及消息过长发送失败的情况
    enable_boot_message: bool = True  # 是否启用启动时的提示消息推送
    debug: bool = False  # 是否开启 debug 模式，开启后会打印更多的日志信息，同时检查更新时不会使用缓存,便于调试

    zip_size: int = 2 * 1024
    gif_zip_size: int = 6 * 1024
    img_format: Optional[str] = None
    img_down_path: Optional[str] = None

    blockquote: bool = True
    black_word: Optional[List[str]] = None

    baidu_id: Optional[str] = None
    baidu_key: Optional[str] = None
    deepl_translator_api_key: Optional[str] = None
    # 配合 deepl_translator 使用的语言检测接口，前往 https://detectlanguage.com/documentation 注册获取 api_key
    single_detection_api_key: Optional[str] = None

    qb_username: Optional[str] = None  # qbittorrent 用户名
    qb_password: Optional[str] = None  # qbittorrent 密码
    qb_web_url: Optional[str] = None
    qb_down_path: Optional[str] = None  # qb 的文件下载地址，这个地址必须是 go-cqhttp 能访问到的
    down_status_msg_group: Optional[List[int]] = None
    down_status_msg_date: int = 10

    pikpak_username: Optional[str] = None  # pikpak 用户名
    pikpak_password: Optional[str] = None  # pikpak 密码
    # pikpak 离线保存的目录, 默认是根目录，示例: ELF_RSS/Downloads ,目录不存在会自动创建, 不能/结尾
    pikpak_download_path: str = ""


config = ELFConfig(**get_driver().config.dict())
logger.debug(f"RSS Config loaded: {config!r}")
