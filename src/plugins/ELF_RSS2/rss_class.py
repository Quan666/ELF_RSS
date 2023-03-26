import re
from copy import deepcopy
from typing import Any, Dict, List, Optional

from tinydb import Query, TinyDB
from tinydb.operations import set as tinydb_set
from yarl import URL

from .config import DATA_PATH, JSON_PATH, config


class Rss:
    def __init__(self, data: Optional[Dict[str, Any]] = None):
        self.name: str = ""  # 订阅名
        self.url: str = ""  # 订阅地址
        self.user_id: List[str] = []  # 订阅用户（qq）
        self.group_id: List[str] = []  # 订阅群组
        self.guild_channel_id: List[str] = []  # 订阅子频道
        self.img_proxy: bool = False
        self.time: str = "5"  # 更新频率 分钟/次
        self.translation: bool = False  # 翻译
        self.only_title: bool = False  # 仅标题
        self.only_pic: bool = False  # 仅图片
        self.only_has_pic: bool = False  # 仅含有图片
        self.download_pic: bool = False  # 是否要下载图片
        self.cookies: str = ""
        self.down_torrent: bool = False  # 是否下载种子
        self.down_torrent_keyword: str = ""  # 过滤关键字，支持正则
        self.black_keyword: str = ""  # 黑名单关键词
        self.is_open_upload_group: bool = True  # 默认开启上传到群
        self.duplicate_filter_mode: List[str] = []  # 去重模式
        self.max_image_number: int = 0  # 图片数量限制，防止消息太长刷屏
        self.content_to_remove: Optional[str] = None  # 正文待移除内容，支持正则
        self.etag: Optional[str] = None
        self.last_modified: Optional[str] = None  # 上次更新时间
        self.error_count: int = 0  # 连续抓取失败的次数，超过 100 就停止更新
        self.stop: bool = False  # 停止更新
        self.pikpak_offline: bool = False  # 是否PikPak离线
        self.pikpak_path_key: str = (
            ""  # PikPak 离线下载路径匹配正则表达式，用于自动归档文件 例如 r"(?:\[.*?\][\s\S])([\s\S]*)[\s\S]-"
        )
        self.send_forward_msg: bool = False  # 当一次更新多条消息时，是否尝试发送合并消息
        if data:
            self.__dict__.update(data)

    # 返回订阅链接
    def get_url(self, rsshub: str = config.rsshub) -> str:
        if URL(self.url).scheme in ["http", "https"]:
            return self.url
        # 先判断地址是否 / 开头
        if self.url.startswith("/"):
            return rsshub + self.url

        return f"{rsshub}/{self.url}"

    # 读取记录
    @staticmethod
    def read_rss() -> List["Rss"]:
        # 如果文件不存在
        if not JSON_PATH.exists():
            return []
        with TinyDB(
            JSON_PATH,
            encoding="utf-8",
            sort_keys=True,
            indent=4,
            ensure_ascii=False,
        ) as db:
            rss_list = [Rss(rss) for rss in db.all()]
        return rss_list

    # 过滤订阅名中的特殊字符
    @staticmethod
    def handle_name(name: str) -> str:
        name = re.sub(r'[?*:"<>\\/|]', "_", name)
        if name == "rss":
            name = "rss_"
        return name

    # 查找是否存在当前订阅名 rss 要转换为 rss_
    @staticmethod
    def get_one_by_name(name: str) -> Optional["Rss"]:
        feed_list = Rss.read_rss()
        return next((feed for feed in feed_list if feed.name == name), None)

    # 添加订阅
    def add_user_or_group_or_channel(
        self,
        user: Optional[str] = None,
        group: Optional[str] = None,
        guild_channel: Optional[str] = None,
    ) -> None:
        if user:
            if user in self.user_id:
                return
            self.user_id.append(user)
        elif group:
            if group in self.group_id:
                return
            self.group_id.append(group)
        elif guild_channel:
            if guild_channel in self.guild_channel_id:
                return
            self.guild_channel_id.append(guild_channel)
        self.upsert()

    # 删除订阅 群组
    def delete_group(self, group: str) -> bool:
        if group not in self.group_id:
            return False
        self.group_id.remove(group)
        with TinyDB(
            JSON_PATH,
            encoding="utf-8",
            sort_keys=True,
            indent=4,
            ensure_ascii=False,
        ) as db:
            db.update(tinydb_set("group_id", self.group_id), Query().name == self.name)  # type: ignore
        return True

    # 删除订阅 子频道
    def delete_guild_channel(self, guild_channel: str) -> bool:
        if guild_channel not in self.guild_channel_id:
            return False
        self.guild_channel_id.remove(guild_channel)
        with TinyDB(
            JSON_PATH,
            encoding="utf-8",
            sort_keys=True,
            indent=4,
            ensure_ascii=False,
        ) as db:
            db.update(
                tinydb_set("guild_channel_id", self.guild_channel_id), Query().name == self.name  # type: ignore
            )
        return True

    # 删除整个订阅
    def delete_rss(self) -> None:
        with TinyDB(
            JSON_PATH,
            encoding="utf-8",
            sort_keys=True,
            indent=4,
            ensure_ascii=False,
        ) as db:
            db.remove(Query().name == self.name)
        self.delete_file()

    # 重命名订阅缓存 json 文件
    def rename_file(self, target: str) -> None:
        source = DATA_PATH / f"{Rss.handle_name(self.name)}.json"
        if source.exists():
            source.rename(target)

    # 删除订阅缓存 json 文件
    def delete_file(self) -> None:
        (DATA_PATH / f"{Rss.handle_name(self.name)}.json").unlink(missing_ok=True)

    # 隐私考虑，不展示除当前群组或频道外的群组、频道和QQ
    def hide_some_infos(
        self, group_id: Optional[int] = None, guild_channel_id: Optional[str] = None
    ) -> "Rss":
        if not group_id and not guild_channel_id:
            return self
        rss_tmp = deepcopy(self)
        rss_tmp.guild_channel_id = [guild_channel_id, "*"] if guild_channel_id else []
        rss_tmp.group_id = [str(group_id), "*"] if group_id else []
        rss_tmp.user_id = ["*"] if rss_tmp.user_id else []
        return rss_tmp

    @staticmethod
    def get_by_guild_channel(guild_channel_id: str) -> List["Rss"]:
        rss_old = Rss.read_rss()
        return [
            rss.hide_some_infos(guild_channel_id=guild_channel_id)
            for rss in rss_old
            if guild_channel_id in rss.guild_channel_id
        ]

    @staticmethod
    def get_by_group(group_id: int) -> List["Rss"]:
        rss_old = Rss.read_rss()
        return [
            rss.hide_some_infos(group_id=group_id)
            for rss in rss_old
            if str(group_id) in rss.group_id
        ]

    @staticmethod
    def get_by_user(user: str) -> List["Rss"]:
        rss_old = Rss.read_rss()
        return [rss for rss in rss_old if user in rss.user_id]

    def set_cookies(self, cookies: str) -> None:
        self.cookies = cookies
        with TinyDB(
            JSON_PATH,
            encoding="utf-8",
            sort_keys=True,
            indent=4,
            ensure_ascii=False,
        ) as db:
            db.update(tinydb_set("cookies", cookies), Query().name == self.name)  # type: ignore

    def upsert(self, old_name: Optional[str] = None) -> None:
        with TinyDB(
            JSON_PATH,
            encoding="utf-8",
            sort_keys=True,
            indent=4,
            ensure_ascii=False,
        ) as db:
            if old_name:
                db.update(self.__dict__, Query().name == old_name)
            else:
                db.upsert(self.__dict__, Query().name == str(self.name))

    def __str__(self) -> str:
        def _generate_feature_string(feature: str, value: Any) -> str:
            return f"{feature}：{value}" if value else ""

        if self.duplicate_filter_mode:
            delimiter = " 或 " if "or" in self.duplicate_filter_mode else "、"
            mode_name = {"link": "链接", "title": "标题", "image": "图片"}
            mode_msg = (
                "已启用去重模式，"
                f"{delimiter.join(mode_name[i] for i in self.duplicate_filter_mode if i != 'or')} 相同时去重"
            )
        else:
            mode_msg = ""

        ret_list = [
            f"名称：{self.name}",
            f"订阅地址：{self.url}",
            _generate_feature_string("订阅QQ", self.user_id),
            _generate_feature_string("订阅群", self.group_id),
            _generate_feature_string("订阅子频道", self.guild_channel_id),
            f"更新时间：{self.time}",
            _generate_feature_string("代理", self.img_proxy),
            _generate_feature_string("翻译", self.translation),
            _generate_feature_string("仅标题", self.only_title),
            _generate_feature_string("仅图片", self.only_pic),
            _generate_feature_string("下载图片", self.download_pic),
            _generate_feature_string("仅含有图片", self.only_has_pic),
            _generate_feature_string("白名单关键词", self.down_torrent_keyword),
            _generate_feature_string("黑名单关键词", self.black_keyword),
            _generate_feature_string("cookies", self.cookies),
            "种子自动下载功能已启用" if self.down_torrent else "",
            "" if self.is_open_upload_group else f"是否上传到群：{self.is_open_upload_group}",
            mode_msg,
            _generate_feature_string("图片数量限制", self.max_image_number),
            _generate_feature_string("正文待移除内容", self.content_to_remove),
            _generate_feature_string("连续抓取失败的次数", self.error_count),
            _generate_feature_string("停止更新", self.stop),
            _generate_feature_string("PikPak离线", self.pikpak_offline),
            _generate_feature_string("PikPak离线路径匹配", self.pikpak_path_key),
        ]
        return "\n".join([i for i in ret_list if i != ""])
