import codecs
import json
import os
import re
from pathlib import Path

import nonebot
from nonebot.log import logger

config = nonebot.get_driver().config

# 存储目录
file_path = str(str(Path.cwd()) + os.sep + 'data' + os.sep)


class rss:
    # 定义基本属性
    name = ''  # 订阅名
    url = ''  # 订阅地址
    user_id = []  # 订阅用户（qq） -1 为空
    group_id = []  # 订阅群组
    img_proxy = False
    sum = 20  # 加载条数
    time = '5'  # 更新频率 分钟/次
    translation = False  # 翻译
    only_title = False  # 仅标题
    only_pic = False  # 仅图片
    cookies = ''
    down_torrent: bool = False  # 是否下载种子
    down_torrent_keyword: str = None  # 过滤关键字，支持正则

    # 定义构造方法
    def __init__(self, name: str, url: str, user_id: str, group_id: str, time='5', img_proxy=False,
                 translation=False, only_title=False, only_pic=False, cookies: str = '', down_torrent: bool = False,
                 down_torrent_keyword: str = None):
        self.name = name
        self.url = url
        if user_id != '-1':
            self.user_id = user_id.split(',')
        else:
            self.user_id = []
        if group_id != '-1':
            self.group_id = group_id.split(',')
        else:
            self.group_id = []
        self.time = time
        self.img_proxy = img_proxy
        self.translation = translation
        self.only_title = only_title
        self.only_pic = only_pic
        if len(cookies) <= 0 or cookies == None:
            self.cookies = None
        else:
            self.cookies = cookies
        self.down_torrent = down_torrent
        self.down_torrent_keyword = down_torrent_keyword

    # 返回订阅链接
    def geturl(self, rsshub: str = config.rsshub) -> str:
        if re.match(u'[hH][tT]{2}[pP][sS]{0,}://', self.url, flags=0):
            return self.url
        else:
            # 先判断地址是否 / 开头
            if re.match(u'/', self.url):
                return rsshub + self.url
            else:
                return rsshub + '/' + self.url

    # 读取记录
    def readRss(self) -> list:
        # 如果文件不存在
        if not os.path.isfile(str(file_path + "rss.json")):
            return []
        rss_list = []
        with codecs.open(str(file_path + "rss.json"), 'r', 'utf-8') as load_f:
            rss_list_json = json.load(load_f)
            for rss_one in rss_list_json:
                tmp_rss = rss('', '', '-1', '-1')
                if type(rss_one) is not str:
                    rss_one = json.dumps(rss_one)
                tmp_rss.__dict__ = json.loads(rss_one)
                rss_list.append(tmp_rss)
        return rss_list

    # 写入记录，传入rss list，不传就把当前 self 写入
    def writeRss(self, rss_new: list = None):
        # 先读取订阅记录
        rss_old = self.readRss()
        # 把当前 self 写入
        if not rss_new:
            rss_new = []
            rss_new.append(self)

        for tmp_new in rss_new:
            flag = True
            for i_old in range(0, len(rss_old)):
                # 如果有记录 就修改记录,没有就添加
                if rss_old[i_old].name == tmp_new.name:
                    rss_old[i_old] = tmp_new
                    flag = False
                    break
            if flag:
                rss_old.append(tmp_new)
        rss_json = []
        for rss_one in rss_old:
            tmp = {}
            tmp.update(rss_one.__dict__)
            rss_json.append(tmp)
        if not os.path.isdir(file_path):
            os.makedirs(file_path)
        with codecs.open(str(file_path + "rss.json"), "w", 'utf-8') as dump_f:
            dump_f.write(json.dumps(rss_json, sort_keys=True,
                                    indent=4, ensure_ascii=False))

    # 查找是否存在当前订阅名 rss 要转换为 rss_
    def findName(self, name: str):
        # 过滤特殊字符
        name = re.sub(r'\?|\*|\:|\"|\<|\>|\\|/|\|', '_', name)
        if name == 'rss':
            name = 'rss_'
        list = self.readRss()
        for tmp in list:
            if tmp.name == name:
                return tmp
        return None

    # 查找是否存在当前订阅链接
    def findURL(self, url: str):
        list = self.readRss()
        for tmp in list:
            if tmp.url == url:
                return tmp
        return None

    # 添加订阅 QQ
    def addUser(self, user: str):
        if str(user) in self.user_id:
            return
        self.user_id.append(str(user))
        self.writeRss()

    # 添加订阅 群组
    def addGroup(self, group: str):
        if str(group) in self.group_id:
            return
        self.group_id.append(str(group))
        self.writeRss()

    # 删除订阅 QQ
    def delUser(self, user: str) -> bool:
        if not str(user) in self.user_id:
            return False
        self.user_id.remove(str(user))
        self.writeRss()
        return True

    # 删除订阅 群组
    def delGroup(self, group: str) -> bool:
        if not str(group) in self.group_id:
            return False
        self.group_id.remove(str(group))
        self.writeRss()
        return True

    # 删除整个订阅
    def delRss(self, delrss):
        rss_old = self.readRss()
        rss_json = []
        for rss_one in rss_old:
            if rss_one.name != delrss.name:
                rss_json.append(json.dumps(
                    rss_one.__dict__, ensure_ascii=False))

        if not os.path.isdir(file_path):
            os.makedirs(file_path)
        with codecs.open(str(file_path + "rss.json"), "w", 'utf-8') as dump_f:
            dump_f.write(json.dumps(rss_json, sort_keys=True,
                                    indent=4, ensure_ascii=False))

    def findGroup(self, group: str) -> list:
        rss_old = self.readRss()
        re = []
        for rss_tmp in rss_old:
            for group_tmp in rss_tmp.group_id:
                if group_tmp == str(group):
                    # 隐私考虑，群组下不展示除当前群组外的群号和QQ
                    rss_tmp.group_id = [str(group), '*']
                    rss_tmp.user_id = ['*']
                    re.append(rss_tmp)
        return re

    def findUser(self, user: str) -> list:
        rss_old = self.readRss()
        re = []
        for rss_tmp in rss_old:
            for group_tmp in rss_tmp.user_id:
                if group_tmp == str(user):
                    re.append(rss_tmp)
        return re

    def setCookies(self, cookies_str: str) -> bool:
        try:
            if len(cookies_str) >= 10:
                cookies = {}
                for line in cookies_str.split(";"):
                    if line.find("=") != -1:
                        name, value = line.strip().split("=")
                        cookies[name] = value
                self.cookies = cookies
                return True
            else:
                self.cookies = None
                return False
        except Exception as e:
            logger.error('{} 的 Cookies 设置时出错！E: {}'.format(self.name, e))
            return False

    def toString(self) -> str:
        if self.cookies:
            cookies_str = '\ncookies:True'
        else:
            cookies_str = ''
        if not config.is_open_auto_down_torrent:
            down_msg = '\n种子自动下载功能未打开'
        else:
            down_msg = ''
        ret = '名称：{}\n订阅地址：{}\n订阅QQ：{}\n订阅群：{}\n更新时间：{}\n代理：{}\n翻译：{}\n仅标题：{}\n仅图片：{}\n下载种子：{}\n下载关键词：{}{}{}'.format(self.name, self.url,
                                                                                                                     str(self.user_id), str(
                                                                                                                         self.group_id), str(self.time), str(self.img_proxy), str(self.translation), str(self.only_title),
                                                                                                                     str(
                                                                                                                         self.only_pic),
                                                                                                                     str(
                                                                                                                         self.down_torrent),
                                                                                                                     str(
                                                                                                                         self.down_torrent_keyword),
                                                                                                                     str(cookies_str), down_msg)
        return ret
