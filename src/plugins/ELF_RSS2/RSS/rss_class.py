import collections
import codecs
import json
import os
import re
from typing import Dict, List
from pathlib import Path

from nonebot.log import logger

from ..config import config

# 存储目录
FILE_PATH = str(str(Path.cwd()) + os.sep + "data" + os.sep)
BASE_RSS_FILE = os.path.join(FILE_PATH, "rss.json")
# rss dropin 目录
RSS_DROPIN_DIR = os.path.join(FILE_PATH, "rss.d")


class Rss:
    # 定义为类属性，可以方便新增属性时不会无法解析配置文件
    name = ""  # 订阅名
    url = ""  # 订阅地址
    user_id = []  # 订阅用户（qq） -1 为空
    group_id = []  # 订阅群组
    img_proxy = False
    sum = 20  # 加载条数
    time = "5"  # 更新频率 分钟/次
    translation = False  # 翻译
    only_title = False  # 仅标题
    only_pic = False  # 仅图片
    only_has_pic = False  # 仅含有图片
    cookies = ""
    down_torrent: bool = False  # 是否下载种子
    down_torrent_keyword: str = None  # 过滤关键字，支持正则
    black_keyword: str = None  # 黑名单关键词
    is_open_upload_group: bool = True  # 默认开启上传到群
    duplicate_filter_mode: [str] = None  # 去重模式
    max_image_number: int = 0  # 图片数量限制，防止消息太长刷屏

    def __init__(
        self,
        name: str,
        url: str,
        user_id: str,
        group_id: str,
        time="5",
        img_proxy=False,
        translation=False,
        only_title=False,
        only_pic=False,
        only_has_pic=False,
        cookies: str = "",
        down_torrent: bool = False,
        down_torrent_keyword: str = None,
        black_keyword: str = None,
        is_open_upload_group: bool = True,
        duplicate_filter_mode: str = None,
        max_image_number: int = 0,
    ):
        self.name = name
        self.url = url
        if user_id != "-1":
            self.user_id = user_id.split(",")
        else:
            self.user_id = []
        if group_id != "-1":
            self.group_id = group_id.split(",")
        else:
            self.group_id = []
        self.time = time
        self.img_proxy = img_proxy
        self.translation = translation
        self.only_title = only_title
        self.only_pic = only_pic
        self.only_has_pic = only_has_pic
        if len(cookies) <= 0 or cookies is None:
            self.cookies = None
        else:
            self.cookies = cookies
        self.down_torrent = down_torrent
        self.down_torrent_keyword = down_torrent_keyword
        self.black_keyword = black_keyword
        self.is_open_upload_group = is_open_upload_group
        self.duplicate_filter_mode = duplicate_filter_mode
        self.max_image_number = max_image_number

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
        rss_list = [rss for rss_list in Rss.read_rss_map().values() for rss in rss_list]
        return rss_list

    @staticmethod
    def read_rss_map(file_name: str = None) -> Dict[str, List["Rss"]]:
        """从 rss.json 和 data/rss.d 读取 rss

        通过指定 `file_name` 以只读取某个特定的 rss 文件。

        Args:
            file_name (Optional[str]): rss 文件路径. 将读取为 f`data/{file_name}`.

        Returns:
            Dict[str, list]: {rss 文件路径: rss 订阅列表}
        """

        def look_up_files(root_, dir_=""):
            """rss 文件遍历"""
            _file_abs_path_list = []
            for _root, _dirs, _files in os.walk(os.path.join(root_, dir_)):
                for _dir in _dirs:
                    _file_abs_path_list.extend(look_up_files(_root, _dir))
                _file_abs_path_list.extend(
                    [(_root, f) for f in _files if os.path.splitext(f)[-1] == ".json"]
                )
                return _file_abs_path_list

        def _read_rss(file_):
            """读取 rss 记录"""
            rss_list = []
            with codecs.open(file_, "r", "utf-8") as load_f:
                rss_list_json = json.load(load_f)
                for rss_one in rss_list_json:
                    tmp_rss = Rss("", "", "-1", "-1")
                    if type(rss_one) is not str:
                        rss_one = json.dumps(rss_one)
                    tmp_rss.__dict__ = json.loads(rss_one)
                    rss_list.append(tmp_rss)
            return rss_list

        rss_list_map = collections.defaultdict(list)

        if file_name:
            to_load_rss_file = os.path.join(FILE_PATH, file_name)
            if not os.path.exists(to_load_rss_file):
                logger.warning(f"No such RSS file as: {file_name}")
            else:
                rss_list_map[to_load_rss_file].extend(_read_rss(to_load_rss_file))
            return rss_list_map

        if os.path.isfile(BASE_RSS_FILE):
            rss_list_map[BASE_RSS_FILE].extend(_read_rss(BASE_RSS_FILE))
        else:
            logger.debug(f"No such RSS file as: {BASE_RSS_FILE}")

        if not os.path.exists(RSS_DROPIN_DIR):
            logger.debug(f"No such RSS Dropin as: {RSS_DROPIN_DIR}")
            os.mkdir(RSS_DROPIN_DIR)
            return rss_list_map

        rss_file_list = look_up_files(RSS_DROPIN_DIR)

        for root, file_name in rss_file_list:
            rss_file = os.path.join(root, file_name)
            logger.debug(f"Loading rss from: {rss_file}")
            rss_list_map[rss_file].extend(_read_rss(rss_file))
        return rss_list_map

    # 写入记录，传入rss list，不传就把当前 self 写入
    def write_rss(self, rss_new: list = None):
        # 把当前 self 写入
        if not rss_new:
            rss_new = [self]

        to_update_rss_file = BASE_RSS_FILE
        for tmp_new in rss_new:
            for rss_file, rss_list in self.read_rss_map().items():
                name_list = [rss.name for rss in rss_list]
                if tmp_new.name in name_list:
                    # 先读取该文件的所有订阅
                    rss_old = rss_list
                    rss_old[name_list.index(tmp_new.name)] = tmp_new
                    to_update_rss_file = rss_file
                    break
            else:
                # 没找到已存在的订阅则追加到 rss.json
                rss_old = self.read_rss_map(to_update_rss_file)[to_update_rss_file]
                rss_old.append(tmp_new)

        rss_json = [rss_one.__dict__ for rss_one in rss_new]
        if not os.path.isdir(FILE_PATH):
            os.makedirs(FILE_PATH)
        with codecs.open(to_update_rss_file, "w", "utf-8") as dump_f:
            dump_f.write(
                json.dumps(rss_json, sort_keys=True, indent=4, ensure_ascii=False)
            )

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

    # 查找是否存在当前订阅链接
    def find_url(self, url: str):
        url_list = self.read_rss()
        for tmp in url_list:
            if tmp.url == url:
                return tmp
        return None

    # 添加订阅 QQ
    def add_user(self, user: str):
        if str(user) in self.user_id:
            return
        self.user_id.append(str(user))
        self.write_rss()

    # 添加订阅 群组
    def add_group(self, group: str):
        if str(group) in self.group_id:
            return
        self.group_id.append(str(group))
        self.write_rss()

    # 删除订阅 QQ
    def delete_user(self, user: str) -> bool:
        if not str(user) in self.user_id:
            return False
        self.user_id.remove(str(user))
        self.write_rss()
        return True

    # 删除订阅 群组
    def delete_group(self, group: str) -> bool:
        if not str(group) in self.group_id:
            return False
        self.group_id.remove(str(group))
        self.write_rss()
        return True

    # 删除整个订阅
    def delete_rss(self, delrss):
        rss_new = []
        to_update_rss_file = BASE_RSS_FILE
        for rss_file, rss_list in self.read_rss_map().items():
            name_list = [rss.name for rss in rss_list]
            if delrss.name in name_list:
                rss_new = rss_list
                rss_new.pop(name_list.index(delrss.name))
                to_update_rss_file = rss_file
                break
        else:
            # 没找到对应的订阅
            logger.warning(f"No such a rss as: {delrss.name}")

        rss_json = [rss_one.__dict__ for rss_one in rss_new]
        if not os.path.isdir(FILE_PATH):
            os.makedirs(FILE_PATH)
        with codecs.open(to_update_rss_file, "w", "utf-8") as dump_f:
            dump_f.write(
                json.dumps(rss_json, sort_keys=True, indent=4, ensure_ascii=False)
            )
        self.delete_file()

    # 删除订阅json文件
    def delete_file(self):
        this_file_path = str(FILE_PATH + self.name + ".json")
        if os.path.exists(this_file_path):
            os.remove(this_file_path)

    def find_group(self, group: str) -> list:
        rss_old = self.read_rss()
        result = []
        for rss_tmp in rss_old:
            for group_tmp in rss_tmp.group_id:
                if group_tmp == str(group):
                    # 隐私考虑，群组下不展示除当前群组外的群号和QQ
                    rss_tmp.group_id = [str(group), "*"]
                    rss_tmp.user_id = ["*"]
                    result.append(rss_tmp)
        return result

    def find_user(self, user: str) -> list:
        rss_old = self.read_rss()
        result = []
        for rss_tmp in rss_old:
            for group_tmp in rss_tmp.user_id:
                if group_tmp == str(user):
                    result.append(rss_tmp)
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
                self.write_rss()
                return True
            else:
                self.cookies = None
                return False
        except Exception as e:
            logger.error(f"{self.name} 的 Cookies 设置时出错！E: {e}")
            return False

    def __str__(self) -> str:
        if self.cookies:
            cookies_str = "\ncookies:True"
        else:
            cookies_str = ""
        if not config.is_open_auto_down_torrent:
            down_msg = "\n种子自动下载功能未打开"
        else:
            down_msg = ""
        mode_name = {"link": "链接", "title": "标题", "image": "图片"}
        if not self.duplicate_filter_mode:
            mode_msg = "\n未启用去重模式"
        else:
            delimiter = "、"
            if "or" in self.duplicate_filter_mode:
                delimiter = " 或 "
            mode_msg = (
                "\n已启用去重模式，"
                f"{delimiter.join(mode_name[i] for i in self.duplicate_filter_mode if i != 'or')}相同时去重"
            )
        ret = (
            f"名称：{self.name}\n"
            f"订阅地址：{self.url}\n"
            f"订阅QQ：{self.user_id}\n"
            f"订阅群：{self.group_id}\n"
            f"更新时间：{self.time}\n"
            f"代理：{self.img_proxy}\n"
            f"翻译：{self.translation}\n"
            f"仅标题：{self.only_title}\n"
            f"仅图片：{self.only_pic}\n"
            f"仅含有图片：{self.only_has_pic}\n"
            f"下载种子：{self.down_torrent}\n"
            f"白名单关键词：{self.down_torrent_keyword}\n"
            f"黑名单关键词：{self.black_keyword}{cookies_str}{down_msg}\n"
            f"是否上传到群：{self.is_open_upload_group}\n"
            f"去重模式：{self.duplicate_filter_mode}{mode_msg}\n"
            f"图片数量限制：{self.max_image_number}\n"
        )
        return ret
