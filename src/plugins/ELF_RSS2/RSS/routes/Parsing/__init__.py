import difflib
import re
import time
from typing import List, Dict
from pyquery import PyQuery as Pq
from nonebot import logger

from ....RSS.rss_class import Rss
from ....config import config


# 订阅器启动的时候将解析器注册到rss实例类？，避免每次推送时再匹配

class ParsingItem:
    def __init__(self, func: object, rex: str = "[^]", priority: int = 10, block: bool = False):
        """
        - **类型**: ``object``
        - **说明**: 解析函数
        """
        self.func: object = func

        """
        - **类型**: ``str``
        - **说明**: 匹配的订阅地址正则，\[^]\ 是全都匹配
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
     - **类型**: ``Dict[str, List[ParsingItem]]``
    - **说明**: 解析器
    """
    handler: Dict[str, List[ParsingItem]] = {
        "title": [],
        "summary": [],
        "source": [],
        "date": [],
        "torrent": []
    }

    # 增加标题解析器
    @classmethod
    def append_handler(cls, parsing_type: str, rex: str = "[^]", priority: int = 10, block: bool = False):
        """
        :说明:
          装饰一个函数来向标题解析器直接添加一个处理函数
        :参数:
          * 无
        """

        def _decorator(func):
            cls.handler.get(parsing_type).append(ParsingItem(func, rex, priority, block))
            cls.handler.update({
                parsing_type: _sort(cls.handler.get(parsing_type))
            })
            return func

        return _decorator


# 处理标题
@ParsingBase.append_handler(parsing_type="title")
async def handle_title(rss: Rss, item: dict, **key) -> str:
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
            if rss.translation:
                res += await handle_translation(content=title)
    except Exception as e:
        logger.info(f"{rss.name} 没有正文内容！ E: {e}")
        res += f"标题：{title}\n"
        if rss.translation:
            res += await handle_translation(content=title)


# 处理来源
@ParsingBase.append_handler(parsing_type="source")
async def handle_source(rss: Rss, item: dict, **key) -> str:
    return f"链接：{item['link']}\n"


# 处理日期
@ParsingBase.append_handler(parsing_type="date")
async def handle_date(rss: Rss, item: dict, **key) -> str:
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
