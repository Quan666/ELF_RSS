import re
from typing import Any, Callable, Dict, List

from tinydb import TinyDB
from tinydb.middlewares import CachingMiddleware
from tinydb.storages import JSONStorage

from ..config import DATA_PATH
from ..rss_class import Rss


# 订阅器启动的时候将解析器注册到rss实例类？，避免每次推送时再匹配
class ParsingItem:
    def __init__(
        self,
        func: Callable[..., Any],
        rex: str = "(.*)",
        priority: int = 10,
        block: bool = False,
    ):
        # 解析函数
        self.func: Callable[..., Any] = func
        # 匹配的订阅地址正则，"(.*)" 是全都匹配
        self.rex: str = rex
        # 优先级，数字越小优先级越高。优先级相同时，会抛弃默认处理方式，即抛弃 rex="(.*)"
        self.priority: int = priority
        # 是否阻止执行之后的处理，默认不阻止。抛弃默认处理方式，只需要 block==True and priority<10
        self.block: bool = block


# 解析器排序
def _sort(_list: List[ParsingItem]) -> List[ParsingItem]:
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
        "picture": [],
        "source": [],
        "date": [],
        "torrent": [],
        "after": [],  # item的最后处理，此处调用消息截取、发送
    }

    """
     - **类型**: ``List[ParsingItem]``
    - **说明**: 最后执行的解析器，在消息发送后，也可以多条消息合并发送
    """
    after_handler: List[ParsingItem] = []

    # 增加解析器
    @classmethod
    def append_handler(
        cls,
        parsing_type: str,
        rex: str = "(.*)",
        priority: int = 10,
        block: bool = False,
    ) -> Callable[..., Any]:
        def _decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            cls.handler[parsing_type].append(ParsingItem(func, rex, priority, block))
            cls.handler.update({parsing_type: _sort(cls.handler[parsing_type])})
            return func

        return _decorator

    @classmethod
    def append_before_handler(
        cls, rex: str = "(.*)", priority: int = 10, block: bool = False
    ) -> Callable[..., Any]:
        def _decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            cls.before_handler.append(ParsingItem(func, rex, priority, block))
            cls.before_handler = _sort(cls.before_handler)
            return func

        return _decorator

    @classmethod
    def append_after_handler(
        cls, rex: str = "(.*)", priority: int = 10, block: bool = False
    ) -> Callable[..., Any]:
        def _decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            cls.after_handler.append(ParsingItem(func, rex, priority, block))
            cls.after_handler = _sort(cls.after_handler)
            return func

        return _decorator


# 对处理器进行过滤
def _handler_filter(_handler_list: List[ParsingItem], _url: str) -> List[ParsingItem]:
    _result = [h for h in _handler_list if re.search(h.rex, _url)]
    # 删除优先级相同时默认的处理器
    _delete = [
        (h.func.__name__, "(.*)", h.priority) for h in _result if h.rex != "(.*)"
    ]
    _result = [
        h for h in _result if (h.func.__name__, h.rex, h.priority) not in _delete
    ]
    return _result


# 解析实例
class ParsingRss:

    # 初始化解析实例
    def __init__(self, rss: Rss):
        self.state: Dict[str, Any] = {}  # 用于存储实例处理中上下文数据
        self.rss: Rss = rss

        # 对处理器进行过滤
        self.before_handler: List[ParsingItem] = _handler_filter(
            ParsingBase.before_handler, self.rss.get_url()
        )
        self.handler: Dict[str, List[ParsingItem]] = {}
        for k, v in ParsingBase.handler.items():
            self.handler[k] = _handler_filter(v, self.rss.get_url())
        self.after_handler = _handler_filter(
            ParsingBase.after_handler, self.rss.get_url()
        )

    # 开始解析
    async def start(self, rss_name: str, new_rss: Dict[str, Any]) -> None:
        # new_data 是完整的 rss 解析后的 dict
        # 前置处理
        rss_title = new_rss["feed"]["title"]
        new_data = new_rss["entries"]
        _file = DATA_PATH / f"{Rss.handle_name(rss_name)}.json"
        db = TinyDB(
            _file,
            storage=CachingMiddleware(JSONStorage),  # type: ignore
            encoding="utf-8",
            sort_keys=True,
            indent=4,
            ensure_ascii=False,
        )
        self.state.update(
            {
                "rss_title": rss_title,
                "new_data": new_data,
                "change_data": [],  # 更新的消息列表
                "conn": None,  # 数据库连接
                "tinydb": db,  # 缓存 json
            }
        )
        for handler in self.before_handler:
            self.state.update(await handler.func(rss=self.rss, state=self.state))
            if handler.block:
                break

        # 分条处理
        self.state.update(
            {
                "messages": [],
                "item_count": 0,
            }
        )
        for item in self.state["change_data"]:
            item_msg = f"【{self.state.get('rss_title')}】更新了!\n----------------------\n"

            for handler_list in self.handler.values():
                # 用于保存上一次处理结果
                tmp = ""
                tmp_state = {"continue": True}  # 是否继续执行后续处理

                # 某一个内容的处理如正文，传入原文与上一次处理结果，此次处理完后覆盖
                for handler in handler_list:
                    tmp = await handler.func(
                        rss=self.rss,
                        state=self.state,
                        item=item,
                        item_msg=item_msg,
                        tmp=tmp,
                        tmp_state=tmp_state,
                    )
                    if handler.block or not tmp_state["continue"]:
                        break
                item_msg += tmp
            self.state["messages"].append(item_msg)

        # 最后处理
        for handler in self.after_handler:
            self.state.update(await handler.func(rss=self.rss, state=self.state))
            if handler.block:
                break
