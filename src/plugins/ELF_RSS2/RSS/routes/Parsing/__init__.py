import difflib
import re
import sqlite3
from email.utils import parsedate_to_datetime
from typing import Any, Callable, Dict, List

import arrow
from nonebot.log import logger
from pyquery import PyQuery as Pq
from tinydb import TinyDB
from tinydb.middlewares import CachingMiddleware
from tinydb.storages import JSONStorage

from ....config import DATA_PATH, config
from ....RSS.rss_class import Rss
from .cache_manage import (
    cache_db_manage,
    cache_filter,
    cache_json_manage,
    duplicate_exists,
    insert_into_cache_db,
)
from .check_update import check_update
from .download_torrent import down_torrent
from .handle_html_tag import handle_bbcode, handle_html_tag
from .handle_images import handle_img
from .handle_translation import handle_translation
from .send_message import send_msg
from .utils import get_proxy, get_summary
from .write_rss_data import write_item


# 订阅器启动的时候将解析器注册到rss实例类？，避免每次推送时再匹配
class ParsingItem:
    def __init__(
        self,
        func: Callable[..., Any],
        rex: str = "(.*)",
        priority: int = 10,
        block: bool = False,
    ):
        """
        - **类型**: ``object``
        - **说明**: 解析函数
        """
        self.func: Callable[..., Any] = func

        """
        - **类型**: ``str``
        - **说明**: 匹配的订阅地址正则，"(.*)" 是全都匹配
        """
        self.rex: str = rex

        """
        - **类型**: ``int``
        - **说明**: 优先级，数字越小优先级越高。优先级相同时，会抛弃默认处理方式，即抛弃 rex="(.*)" 
        """
        self.priority: int = priority

        """
        - **类型**: ``bool``
        - **说明**: 是否阻止执行之后的处理，默认不阻止。抛弃默认处理方式，只需要 block==True and priority<10
        """
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
        h for h in _result if not ((h.func.__name__, h.rex, h.priority) in _delete)
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
        _file = DATA_PATH / (rss_name + ".json")
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


# 检查更新
@ParsingBase.append_before_handler(priority=10)
async def handle_check_update(rss: Rss, state: Dict[str, Any]):
    db = state.get("tinydb")
    change_data = await check_update(db, state.get("new_data"))
    return {"change_data": change_data}


# 判断是否满足推送条件
@ParsingBase.append_before_handler(priority=11)
async def handle_check_update(rss: Rss, state: Dict[str, Any]):
    change_data = state.get("change_data")
    db = state.get("tinydb")
    for item in change_data.copy():
        summary = get_summary(item)
        # 检查是否包含屏蔽词
        if config.black_word and re.findall("|".join(config.black_word), summary):
            logger.info("内含屏蔽词，已经取消推送该消息")
            write_item(db, item)
            change_data.remove(item)
            continue
        # 检查是否匹配关键词 使用 down_torrent_keyword 字段,命名是历史遗留导致，实际应该是白名单关键字
        if rss.down_torrent_keyword and not re.search(
            rss.down_torrent_keyword, summary
        ):
            write_item(db, item)
            change_data.remove(item)
            continue
        # 检查是否匹配黑名单关键词 使用 black_keyword 字段
        if rss.black_keyword and (
            re.search(rss.black_keyword, item["title"])
            or re.search(rss.black_keyword, summary)
        ):
            write_item(db, item)
            change_data.remove(item)
            continue
        # 检查是否只推送有图片的消息
        if (rss.only_pic or rss.only_has_pic) and not re.search(
            r"<img[^>]+>|\[img]", summary
        ):
            logger.info(f"{rss.name} 已开启仅图片/仅含有图片，该消息没有图片，将跳过")
            write_item(db, item)
            change_data.remove(item)

    return {"change_data": change_data}


# 如果启用了去重模式，对推送列表进行过滤
@ParsingBase.append_before_handler(priority=12)
async def handle_check_update(rss: Rss, state: Dict[str, Any]):
    change_data = state.get("change_data")
    conn = state.get("conn")
    db = state.get("tinydb")

    # 检查是否启用去重 使用 duplicate_filter_mode 字段
    if not rss.duplicate_filter_mode:
        return {"change_data": change_data}

    if not conn:
        conn = sqlite3.connect(str(DATA_PATH / "cache.db"))
        conn.set_trace_callback(logger.debug)

    await cache_db_manage(conn)

    delete = []
    for index, item in enumerate(change_data):
        is_duplicate, image_hash = await duplicate_exists(
            rss=rss,
            conn=conn,
            item=item,
            summary=get_summary(item),
        )
        if is_duplicate:
            write_item(db, item)
            delete.append(index)
        else:
            change_data[index]["image_hash"] = str(image_hash)

    change_data = [
        item for index, item in enumerate(change_data) if index not in delete
    ]

    return {
        "change_data": change_data,
        "conn": conn,
    }


# 处理标题
@ParsingBase.append_handler(parsing_type="title")
async def handle_title(
    rss: Rss,
    state: Dict[str, Any],
    item: Dict[str, Any],
    item_msg: str,
    tmp: str,
    tmp_state: Dict[str, Any],
) -> str:
    # 判断是否开启了只推送图片
    if rss.only_pic:
        return ""

    title = item["title"]

    if not config.blockquote:
        title = re.sub(r" - 转发 .*", "", title)

    res = f"标题：{title}\n"
    # 隔开标题和正文
    if not rss.only_title:
        res += "\n"
    if rss.translation:
        res += await handle_translation(content=title)

    # 如果开启了只推送标题，跳过下面判断标题与正文相似度的处理
    if rss.only_title:
        return res

    # 判断标题与正文相似度，避免标题正文一样，或者是标题为正文前N字等情况
    try:
        summary_html = Pq(get_summary(item))
        if not config.blockquote:
            summary_html.remove("blockquote")
        similarity = difflib.SequenceMatcher(
            None, summary_html.text()[: len(title)], title
        )
        # 标题正文相似度
        if similarity.ratio() > 0.6:
            res = ""
    except Exception as e:
        logger.warning(f"{rss.name} 没有正文内容！{e}")

    return res


# 处理正文 判断是否是仅推送标题 、是否仅推送图片
@ParsingBase.append_handler(parsing_type="summary", priority=1)
async def handle_summary(
    rss: Rss,
    state: Dict[str, Any],
    item: Dict[str, Any],
    item_msg: str,
    tmp: str,
    tmp_state: Dict[str, Any],
) -> str:
    if rss.only_title or rss.only_pic:
        tmp_state["continue"] = False
    return ""


# 处理正文 处理网页 tag
@ParsingBase.append_handler(parsing_type="summary", priority=10)
async def handle_summary(
    rss: Rss,
    state: Dict[str, Any],
    item: Dict[str, Any],
    item_msg: str,
    tmp: str,
    tmp_state: Dict[str, Any],
) -> str:
    try:
        tmp += await handle_html_tag(html=Pq(get_summary(item)))
    except Exception as e:
        logger.warning(f"{rss.name} 没有正文内容！{e}")
    return tmp


# 处理正文 移出指定内容
@ParsingBase.append_handler(parsing_type="summary", priority=11)
async def handle_summary(
    rss: Rss,
    state: Dict[str, Any],
    item: Dict[str, Any],
    item_msg: str,
    tmp: str,
    tmp_state: Dict[str, Any],
) -> str:
    # 移除指定内容
    if rss.content_to_remove:
        for pattern in rss.content_to_remove:
            tmp = re.sub(pattern, "", tmp)
    return tmp


# 处理正文 翻译
@ParsingBase.append_handler(parsing_type="summary", priority=12)
async def handle_summary(
    rss: Rss,
    state: Dict[str, Any],
    item: Dict[str, Any],
    item_msg: str,
    tmp: str,
    tmp_state: Dict[str, Any],
) -> str:
    if rss.translation:
        tmp += await handle_translation(tmp)
    return tmp


# 处理图片
@ParsingBase.append_handler(parsing_type="picture")
async def handle_picture(
    rss: Rss,
    state: Dict[str, Any],
    item: Dict[str, Any],
    item_msg: str,
    tmp: str,
    tmp_state: Dict[str, Any],
) -> str:

    # 判断是否开启了只推送标题
    if rss.only_title:
        return ""

    res = ""
    try:
        res += await handle_img(
            item=item,
            img_proxy=rss.img_proxy,
            img_num=rss.max_image_number,
        )
    except Exception as e:
        logger.warning(f"{rss.name} 没有正文内容！{e}")

    # 判断是否开启了只推送图片
    if rss.only_pic:
        return f"{res}\n"

    return f"{tmp + res}\n"


# 处理来源
@ParsingBase.append_handler(parsing_type="source")
async def handle_source(
    rss: Rss,
    state: Dict[str, Any],
    item: Dict[str, Any],
    item_msg: str,
    tmp: str,
    tmp_state: Dict[str, Any],
) -> str:
    return f"链接：{item['link']}\n"


# 处理种子
@ParsingBase.append_handler(parsing_type="torrent")
async def handle_torrent(
    rss: Rss,
    state: Dict[str, Any],
    item: Dict[str, Any],
    item_msg: str,
    tmp: str,
    tmp_state: Dict[str, Any],
) -> str:
    res = ""
    if not rss.is_open_upload_group:
        rss.group_id = []
    if rss.down_torrent:
        # 处理种子
        try:
            hash_list = await down_torrent(
                rss=rss, item=item, proxy=get_proxy(rss.img_proxy)
            )
            if hash_list and hash_list[0] is not None:
                res = "\n磁力：\n" + "\n".join(
                    [f"magnet:?xt=urn:btih:{h}" for h in hash_list]
                )
        except Exception:
            logger.exception("下载种子时出错")
    return res


# 处理日期
@ParsingBase.append_handler(parsing_type="date")
async def handle_date(
    rss: Rss,
    state: Dict[str, Any],
    item: Dict[str, Any],
    item_msg: str,
    tmp: str,
    tmp_state: Dict[str, Any],
) -> str:
    date = item.get("published", item.get("updated"))
    if date:
        try:
            date = parsedate_to_datetime(date)
        except TypeError:
            pass
        finally:
            date = arrow.get(date).to("Asia/Shanghai")
    else:
        date = arrow.now()
    return f"日期：{date.format('YYYY年MM月DD日 HH:mm:ss')}"


# 发送消息
@ParsingBase.append_handler(parsing_type="after")
async def handle_message(
    rss: Rss,
    state: Dict[str, Any],
    item: Dict[str, Any],
    item_msg: str,
    tmp: str,
    tmp_state: Dict[str, Any],
) -> str:
    db = state["tinydb"]

    # 发送消息并写入文件
    if await send_msg(rss=rss, msg=item_msg, item=item):

        if rss.duplicate_filter_mode:
            await insert_into_cache_db(
                conn=state["conn"], item=item, image_hash=item["image_hash"]
            )

        if item.get("to_send"):
            item.pop("to_send")

        state["item_count"] += 1
    else:
        item["to_send"] = True
        if not item.get("count"):
            item["count"] = 1
        else:
            item["count"] += 1

    write_item(db, item)

    return ""


@ParsingBase.append_after_handler()
async def after_handler(rss: Rss, state: Dict[str, Any]) -> Dict[str, Any]:
    item_count: int = state["item_count"]
    conn = state["conn"]
    db = state["tinydb"]

    if item_count > 0:
        logger.info(f"{rss.name} 新消息推送完毕，共计：{item_count}")
    else:
        logger.info(f"{rss.name} 没有新信息")

    if conn is not None:
        conn.close()

    new_data_length = len(state["new_data"])
    await cache_json_manage(db, new_data_length)
    db.close()

    return {}
