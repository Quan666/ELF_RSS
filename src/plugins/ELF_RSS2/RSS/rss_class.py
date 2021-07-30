import codecs
import json
import os
import re
from pathlib import Path

from nonebot.log import logger

from ..config import config

# 存储目录
FILE_PATH = str(str(Path.cwd()) + os.sep + "data" + os.sep)


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
    content_to_remove: [str] = None  # 正文待移除内容，支持正则
    stop = False  # 停止更新

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
        content_to_remove: str = None,
        stop=False,
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
        self.content_to_remove = content_to_remove
        self.stop = stop

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
        if not os.path.isfile(str(FILE_PATH + "rss.json")):
            return []
        rss_list = []
        with codecs.open(str(FILE_PATH + "rss.json"), "r", "utf-8") as load_f:
            rss_list_json = json.load(load_f)
            for rss_one in rss_list_json:
                tmp_rss = Rss("", "", "-1", "-1")
                if not isinstance(rss_one, str):
                    rss_one = json.dumps(rss_one)
                tmp_rss.__dict__ = json.loads(rss_one)
                rss_list.append(tmp_rss)
        return rss_list

    # 写入记录，传入rss list，不传就把当前 self 写入
    def write_rss(self, rss_new: list = None):
        # 先读取订阅记录
        rss_old = self.read_rss()
        # 把当前 self 写入
        if not rss_new:
            rss_new = [self]

        for tmp_new in rss_new:
            flag = True
            for index, i_old in enumerate(rss_old):
                # 如果有记录 就修改记录,没有就添加
                if i_old.name == tmp_new.name:
                    rss_old[index] = tmp_new
                    flag = False
                    break
            if flag:
                rss_old.append(tmp_new)
        rss_json = []
        for rss_one in rss_old:
            tmp = {}
            tmp.update(rss_one.__dict__)
            rss_json.append(tmp)
        if not os.path.isdir(FILE_PATH):
            os.makedirs(FILE_PATH)
        with codecs.open(str(FILE_PATH + "rss.json"), "w", "utf-8") as dump_f:
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

    # 删除订阅 群组
    def delete_group(self, group: str) -> bool:
        if not str(group) in self.group_id:
            return False
        self.group_id.remove(str(group))
        self.write_rss()
        return True

    # 删除整个订阅
    def delete_rss(self, delrss):
        rss_old = self.read_rss()
        rss_json = []
        for rss_one in rss_old:
            if rss_one.name != delrss.name:
                rss_json.append(rss_one.__dict__)

        if not os.path.isdir(FILE_PATH):
            os.makedirs(FILE_PATH)
        with codecs.open(str(FILE_PATH + "rss.json"), "w", "utf-8") as dump_f:
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
                self.write_rss()
                return True
            else:
                self.cookies = None
                return False
        except Exception as e:
            logger.error(f"{self.name} 的 Cookies 设置时出错！E: {e}")
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
