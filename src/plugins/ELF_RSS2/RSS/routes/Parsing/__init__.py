import difflib
import re
import time
from typing import List, Dict
from pyquery import PyQuery as Pq
from nonebot import logger

from . import check_update, send_message
from ....RSS.rss_class import Rss
from ....config import config


# 订阅器启动的时候将解析器注册到rss实例类？，避免每次推送时再匹配

class ParsingItem:
    def __init__(self, func: callable, rex: str = "(.*)", priority: int = 10, block: bool = False):
        """
        - **类型**: ``object``
        - **说明**: 解析函数
        """
        self.func: callable = func

        """
        - **类型**: ``str``
        - **说明**: 匹配的订阅地址正则，\(.*)\ 是全都匹配
        """
        self.rex: str = rex

        """
        - **类型**: ``int``
        - **说明**: 优先级，数字越小优先级越高。优先级相同时，不要相互依赖处理结果，即处理A需要在处理B的结果之上进行处理。
        """
        self.priority: int = priority

        """
        - **类型**: ``bool``
        - **说明**: 是否阻止执行之后的处理，默认不阻止。抛弃默认处理方式，只需要 block==True and priority<10
        """
        self.block: bool = block


# 解析器排序
def _sort(_list):
    _list.sort(key=lambda x: x.priority)
    return _list


# rss 解析类 ，需要将特殊处理的订阅注册到该类
class ParsingBase:
    """
     - **类型**: ``List[ParsingItem]``
    - **说明**: 最先执行的解析器,定义了检查更新等前置步骤
    """
    before_handler: List[ParsingItem] = []

    """
     - **类型**: ``Dict[str, List[ParsingItem]]``
    - **说明**: 解析器
    """
    handler: Dict[str, List[ParsingItem]] = {
        "before": [],  # item的预处理
        "title": [],
        "summary": [],
        "source": [],
        "date": [],
        "torrent": [],
        "after": []  # item的最后处理，此处调用消息截取、发送
    }

    """
     - **类型**: ``List[ParsingItem]``
    - **说明**: 最后执行的解析器，在消息发送后，也可以多条消息合并发送
    """
    after_handler: List[ParsingItem] = []

    # 增加解析器
    @classmethod
    def append_handler(cls, parsing_type: str, rex: str = "(.*)", priority: int = 10, block: bool = False):
        def _decorator(func):
            cls.handler.get(parsing_type).append(ParsingItem(func, rex, priority, block))
            cls.handler.update({
                parsing_type: _sort(cls.handler.get(parsing_type))
            })
            return func

        return _decorator

    @classmethod
    def append_before_handler(cls, rex: str = "(.*)", priority: int = 10, block: bool = False):
        def _decorator(func):
            cls.before_handler.append(ParsingItem(func, rex, priority, block))
            cls.before_handler = _sort(cls.before_handler)
            return func

        return _decorator

    @classmethod
    def append_after_handler(cls, rex: str = "(.*)", priority: int = 10, block: bool = False):
        def _decorator(func):
            cls.after_handler.append(ParsingItem(func, rex, priority, block))
            cls.after_handler = _sort(cls.after_handler)
            return func

        return _decorator


# 解析实例
class ParsingRss(ParsingBase):

    # 初始化解析实例
    def __init__(self, rss: Rss):
        self.state = {}  # 用于存储实例处理中上下文数据
        self.rss = rss
        for i in range(0, len(ParsingBase.before_handler)):
            if re.search(ParsingBase.before_handler[i].rex, self.rss.get_url()):
                self.before_handler.append(ParsingBase.before_handler[i])
        for k, v in ParsingBase.handler.items():
            self.handler.update({k: []})
            for h in v:
                if re.search(h.rex, self.rss.get_url()):
                    self.handler[k].append(h)
        for h in ParsingBase.after_handler:
            if re.search(h.rex, self.rss.get_url()):
                self.after_handler.append(h)

    # 开始解析
    async def start(self, new_data: dict, old_data: list):
        # new_data 是完整的 rss 解析后的 dict，old_data 是 list
        # 前置处理
        self.state.update({
            "rss_title": new_data.get('feed').get('title'),
            "new_data": new_data.get("entries"),
            "old_data": old_data,
            "change_data": []  # 更新的消息列表
        })
        for h in self.before_handler:
            self.state.update(await h.func(rss=self.rss, state=self.state))
            if h.block:
                break

        # 分条处理
        self.state.update({
            "messages": [],
        })
        for item in self.state.get("change_data"):
            item_msg = f"【{self.state.get('rss_title')}】更新了!\n----------------------\n"
            for k, v in self.handler.items():
                tmp = ""  # 用于保存上一次处理结果
                for h in v:
                    if t := (await h.func(rss=self.rss, item=item, item_msg=item_msg, tmp=tmp)):
                        tmp = t
                    else:
                        tmp = ""
                    if h.block:
                        break
                item_msg += tmp
            self.state.get("messages").append(item_msg)

        # 最后处理
        for h in self.after_handler:
            self.state.update(await h.func(rss=self.rss, state=self.state))
            if h.block:
                break


# 检查更新
@ParsingBase.append_before_handler()
async def handle_check_update(rss: Rss, state: dict):
    return {
        "change_data": await check_update.check_update(state.get("new_data"), state.get("old_data"))
    }


# 处理标题
@ParsingBase.append_handler(parsing_type="title")
async def handle_title(rss: Rss, item: dict, item_msg: str, tmp: str) -> str:
    # 处理标题
    title = item["title"]
    res = ""
    if not config.blockquote:
        title = re.sub(r" - 转发 .*", "", title)
    # 先判断与正文相识度，避免标题正文一样，或者是标题为正文前N字等情况
    try:
        summary_html = Pq(item["summary"])
        if not config.blockquote:
            summary_html.remove("blockquote")
        similarity = difflib.SequenceMatcher(
            None, summary_html.text()[: len(title)], title
        )
        # 标题正文相似度
        if rss.only_pic or similarity.ratio() <= 0.6:
            res += f"标题：{title}\n"
            # if rss.translation:
            #     res += await handle_translation(content=title)
    except Exception as e:
        logger.info(f"{rss.name} 没有正文内容！ E: {e}")
        res += f"标题：{title}\n"
        # if rss.translation:
        #     res += await handle_translation(content=title)
    return res


# 处理正文
@ParsingBase.append_handler(parsing_type="summary",priority=10)
async def handle_summary(rss: Rss, item: dict, item_msg: str, tmp: str) -> str:
    return tmp
    pass


# 处理来源
@ParsingBase.append_handler(parsing_type="source")
async def handle_source(rss: Rss, item: dict, item_msg: str, tmp: str) -> str:
    return f"链接：{item['link']}\n"


# 处理日期
@ParsingBase.append_handler(parsing_type="date")
async def handle_date(rss: Rss, item: dict, item_msg: str, tmp: str) -> str:
    date = item.get("published_parsed")
    if date:
        rss_time = time.mktime(date)
        # 时差处理，待改进
        if rss_time + 28800.0 <= time.time():
            rss_time += 28800.0
        return "日期：" + time.strftime("%m月%d日 %H:%M:%S", time.localtime(rss_time))
    # 没有日期的情况，以当前时间
    else:
        return "日期：" + time.strftime("%m月%d日 %H:%M:%S", time.localtime())


# 发送消息
@ParsingBase.append_handler(parsing_type="after")
async def handle_message(rss: Rss, item: dict, item_msg: str, tmp: str) -> str:
    # 发送消息并写入文件
    if await send_message.send_msg(rss=rss, msg=item_msg, item=item):
        # write_item(rss=rss, new_rss=new_rss, new_item=item)
        pass
    return tmp
