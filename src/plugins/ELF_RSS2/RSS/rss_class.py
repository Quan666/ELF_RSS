import re

from nonebot.log import logger
from pathlib import Path
from tinydb import TinyDB, Query
from tinydb.operations import set

from ..config import config
from ..config import DATA_PATH, JSON_PATH


class Rss:
    def __init__(self):
        self.name = ""  # 订阅名
        self.url = ""  # 订阅地址
        self.user_id = []  # 订阅用户（qq） -1 为空
        self.group_id = []  # 订阅群组
        self.img_proxy = False
        self.time = "5"  # 更新频率 分钟/次
        self.translation = False  # 翻译
        self.only_title = False  # 仅标题
        self.only_pic = False  # 仅图片
        self.only_has_pic = False  # 仅含有图片
        self.cookies = ""
        self.down_torrent = False  # 是否下载种子
        self.down_torrent_keyword = ""  # 过滤关键字，支持正则
        self.black_keyword = ""  # 黑名单关键词
        self.is_open_upload_group = True  # 默认开启上传到群
        self.duplicate_filter_mode = None  # 去重模式
        self.max_image_number = 0  # 图片数量限制，防止消息太长刷屏
        self.content_to_remove = None  # 正文待移除内容，支持正则
        self.stop = False  # 停止更新

    # 返回订阅链接
    def get_url(self, rsshub: str = config.rsshub) -> str:
        if re.match("[hH][tT]{2}[pP][sS]?://", self.url, flags=0):
            return self.url
        else:
            # 先判断地址是否 / 开头
            if re.match("/", self.url):
                return rsshub + self.url
            else:
                return rsshub + "/" + self.url

    # 读取记录
    @staticmethod
    def read_rss() -> list:
        # 如果文件不存在
        if not Path.exists(JSON_PATH):
            return []
        rss_list = []
        db = TinyDB(
            JSON_PATH,
            encoding="utf-8",
            sort_keys=True,
            indent=4,
            ensure_ascii=False,
        )
        for rss in db.all():
            tmp_rss = Rss()
            tmp_rss.__dict__.update(rss)
            rss_list.append(tmp_rss)
        return rss_list

    # 查找是否存在当前订阅名 rss 要转换为 rss_
    def find_name(self, name: str):
        # 过滤特殊字符
        name = re.sub(r'[?*:"<>\\/|]', "_", name)
        if name == "rss":
            name = "rss_"
        feed_list = self.read_rss()
        for feed in feed_list:
            if feed.name == name:
                return feed
        return None

    # 添加订阅
    def add_user_or_group(self, user: str = None, group: str = None):
        if user:
            if str(user) in self.user_id:
                return
            self.user_id.append(str(user))
        else:
            if str(group) in self.group_id:
                return
            self.group_id.append(str(group))
        db = TinyDB(
            JSON_PATH,
            encoding="utf-8",
            sort_keys=True,
            indent=4,
            ensure_ascii=False,
        )
        db.upsert(self.__dict__, Query().name == self.name)

    # 删除订阅 群组
    def delete_group(self, group: str) -> bool:
        if not str(group) in self.group_id:
            return False
        self.group_id.remove(str(group))
        db = TinyDB(
            JSON_PATH,
            encoding="utf-8",
            sort_keys=True,
            indent=4,
            ensure_ascii=False,
        )
        db.update(set("group_id", self.group_id), Query().name == self.name)
        return True

    # 删除整个订阅
    def delete_rss(self):
        db = TinyDB(
            JSON_PATH,
            encoding="utf-8",
            sort_keys=True,
            indent=4,
            ensure_ascii=False,
        )
        db.remove(Query().name == self.name)
        self.delete_file()

    # 重命名订阅缓存 json 文件
    def rename_file(self, target: str):
        this_file_path = DATA_PATH / (self.name + ".json")
        if Path.exists(this_file_path):
            this_file_path.rename(target)

    # 删除订阅缓存 json 文件
    def delete_file(self):
        this_file_path = DATA_PATH / (self.name + ".json")
        Path.unlink(this_file_path, missing_ok=True)

    def find_group(self, group: str) -> list:
        rss_old = self.read_rss()
        result = []
        for rss_tmp in rss_old:
            if rss_tmp.group_id and group in rss_tmp.group_id:
                # 隐私考虑，群组下不展示除当前群组外的群号和QQ
                rss_tmp.group_id = [group, "*"]
                rss_tmp.user_id = ["*"]
                result.append(rss_tmp)
        return result

    def find_user(self, user: str) -> list:
        rss_old = self.read_rss()
        result = [rss for rss in rss_old if user in rss.user_id]
        return result

    def set_cookies(self, cookies_str: str) -> bool:
        try:
            if len(cookies_str) >= 10:
                cookies = {}
                for line in cookies_str.split(";"):
                    if line.find("=") != -1:
                        name, value = line.strip().split("=")
                        cookies[name] = value
                self.cookies = cookies
                db = TinyDB(
                    JSON_PATH,
                    encoding="utf-8",
                    sort_keys=True,
                    indent=4,
                    ensure_ascii=False,
                )
                db.update(set("cookies", cookies), Query().name == self.name)
                return True
            else:
                self.cookies = None
                return False
        except Exception as e:
            logger.error(f"{self.name} 的 Cookies 设置时出错！\n{e}")
            return False

    def __str__(self) -> str:
        mode_name = {"link": "链接", "title": "标题", "image": "图片"}
        if self.duplicate_filter_mode:
            delimiter = "、"
            if "or" in self.duplicate_filter_mode:
                delimiter = " 或 "
            mode_msg = (
                "已启用去重模式，"
                f"{delimiter.join(mode_name[i] for i in self.duplicate_filter_mode if i != 'or')} 相同时去重"
            )
        ret_list = (
            lambda: f"名称：{self.name}\n",
            lambda: f"订阅地址：{self.url}\n",
            lambda: f"订阅QQ：{self.user_id}\n" if self.user_id else "",
            lambda: f"订阅群：{self.group_id}\n" if self.group_id else "",
            lambda: f"更新时间：{self.time}\n",
            lambda: f"代理：{self.img_proxy}\n" if self.img_proxy else "",
            lambda: f"翻译：{self.translation}\n" if self.translation else "",
            lambda: f"仅标题：{self.only_title}\n" if self.only_title else "",
            lambda: f"仅图片：{self.only_pic}\n" if self.only_pic else "",
            lambda: f"仅含有图片：{self.only_has_pic}\n" if self.only_has_pic else "",
            lambda: f"白名单关键词：{self.down_torrent_keyword}\n"
            if self.down_torrent_keyword
            else "",
            lambda: f"黑名单关键词：{self.black_keyword}\n" if self.black_keyword else "",
            lambda: "cookies：True\n" if self.cookies else "",
            lambda: f"下载种子：{self.down_torrent}\n"
            if self.down_torrent
            else "种子自动下载功能未打开\n",
            lambda: f"是否上传到群：{self.is_open_upload_group}\n"
            if self.is_open_upload_group
            else "",
            lambda: f"{mode_msg}\n" if self.duplicate_filter_mode else "",
            lambda: f"图片数量限制：{self.max_image_number}\n"
            if self.max_image_number
            else "",
            lambda: f"正文待移除内容：{self.content_to_remove}\n"
            if self.content_to_remove
            else "",
            lambda: f"停止更新：{self.stop}\n" if self.stop else "",
        )
        ret = ""
        for r in ret_list:
            ret += r()
        return ret
