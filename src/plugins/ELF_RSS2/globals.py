from contextvars import ContextVar
from functools import partial
import copy
from operator import delitem, setitem, getitem
import typing as t
from .rss_class import Rss
from .typings.t_globals import Item, NewRss


class State:
    """可用来存取上下文临时数据"""

    def __init__(self) -> None:
        self.new_rss: t.Optional[NewRss] = None  # 存储fetch_rss获取的数据 在获取最新rss时存入
        self.sn: int = 0  # 图片初始序号 在route的picture handel中,每处理一张图片应该将该值+1
        self.img_num: int = 1  # 单次更新包含的图片数量  应在route的picture handel内处理后存入
        self.item: t.Optional[
            Item
        ] = None  # change_data里的一个更新, 应在循环change_data的时候存入其中的子项
        self.id: str = ""  # 每次更新的唯一ID 应在route的before handel内处理后存入


class RequestContext:
    def __init__(self, rss: Rss) -> None:
        self.state = State()
        self.rss = rss

    def push(self):
        """将自身入栈"""
        top = _app_context.top  
        if top is not None:
            top.pop()
        _app_context.push(self)

    def pop(self):
        """
        从请求上下文中弹出,防止可能的内存泄露
        """
        rv = _app_context.pop()
        assert rv is self, "弹出上下文时出现意料之外的错误"


class Local(object):
    """
    用于保存上下文全局数据的本地对象
    每个进程上下文之间可以安全的访问数据
    """

    def __init__(self) -> None:
        super().__setattr__("_store", ContextVar("local_store"))

    def __getattr__(self, name: str) -> t.Any:
        values = self._store.get({})
        try:
            return values[name]
        except KeyError:
            raise AttributeError(name)

    def __setattr__(self, name: str, value: t.Any) -> None:
        values = self._store.get({}).copy()
        values[name] = value
        self._store.set(values)

    def __delattr__(self, name: str) -> None:
        values = self._store.get({}).copy()
        try:
            del values[name]
            self._store.set(values)
        except KeyError:
            raise AttributeError(name)

    def release_local(self) -> None:
        """主动的释放上下文空间"""
        self._store.set({})

    def __call__(self, name: str) -> "LocalProxy":
        """
        一个创建代理类的快捷方式
        参数:
            name: 需要代理的属性

        返回值:
            一个代理了自身name属性的LocalProxy对象
        """
        return LocalProxy(self, name)


class LocalStack:
    def __init__(self) -> None:
        self._local = Local()

    def push(self, obj: t.Any) -> t.List[t.Any]:
        """将数据推入栈中"""
        rv = getattr(self._local, "stack", []).copy()
        rv.append(obj)
        self._local.stack = rv
        return rv

    def pop(self) -> t.Any:
        """执行出栈操作"""
        stack = getattr(self._local, "stack", None)
        if stack is None:
            return stack
        elif len(stack) == 1:
            self._local.release_local()
            return stack[-1]
        else:
            return stack.pop()

    @property
    def top(self) -> t.Any:
        # 返回栈顶数据,如不存在则返回None
        try:
            return self._local.stack[-1]
        except (AttributeError, IndexError):
            return None


class ProxyLookup:
    """
    为另外一个类的类的属性进行服务,对属性进行赋值,获取,删除时会使用该类的属性
    """

    def __init__(
        self, f: t.Optional[t.Callable] = None, fallback: t.Optional[t.Callable] = None
    ) -> None:
        """
        参数:
            f: 描述器用于获取属性的具体函数,会使用这个函数来获取属性
            fallback: 如果获取代理属性出错的时候会把这个回调函数作为属性绑定
        """
        if hasattr(f, "__get__"):
            # 有__get__属性代表是一个python函数,用__get__绑定到实例

            def bind(instance: "LocalProxy", obj: t.Any) -> t.Any:
                return f.__get__(obj, type(obj))  # 绑定为实例方法

        elif f is not None:
            # 其他的代表为builtin函数，用另一种方法代理
            # https://docs.python.org/zh-cn/3/library/functions.html

            def bind(instance: "LocalProxy", obj: t.Any) -> t.Any:
                """
                对函数进行柯里化,固定f的第一个参数为obj(代理对象实例)
                使解释器能够正常处理
                """
                return partial(f, obj)

        else:
            bind = None
        self.bind = bind
        self.fallback = fallback

    def __set_name__(self, owner: "LocalProxy", name: str):
        """类被初始化的时候会被自动回调

        参数:
            owner (LocalProxy): 所有者类
            name (str): 类属性名
        """
        self.name = name

    def __get__(self, instance: "LocalProxy", owner) -> t.Any:
        if instance is None:
            return self
        try:
            obj = instance._get_object()
        except RuntimeError:
            if self.fallback is not None:
                # 将fallback绑定为实例方法返回
                return self.fallback.__get__(instance, owner)
            else:
                raise
        if self.bind is not None:
            # 如果是被绑定的函数就用处理过的函数返回
            return self.bind(instance=instance, obj=obj)
        else:
            return getattr(obj, self.name)


class LocalProxy(object):
    """
    一个代理对象,用于安全便捷的访问Local实例

    参数:
        local: 需要被代理的实例
        name: 代理名称
    """

    def __init__(self, local: Local, name: str = t.Optional[str]) -> None:
        super().__setattr__("_local", local)  # 被代理的对象
        super().__setattr__("_name", name)  # 代理的属性值

    def _get_object(self) -> t.Any:
        """
        获取当前代理的原始对象
        """

        if not hasattr(self._local, "release_local"):
            # 如果代理的不是Local实例,就返回该实例调用返回值
            return self._local()
        try:
            return getattr(self._local, self._name)
        except AttributeError:
            raise RuntimeError(f"代理对象不存在{self._name}属性")

    # 对这些常用的魔术方法都进行代理操作
    __getattr__ = ProxyLookup(getattr)
    __setattr__ = ProxyLookup(setattr)
    __delattr__ = ProxyLookup(delattr)
    __hasattr__ = ProxyLookup(hasattr)
    __getitem__ = ProxyLookup(getitem)
    __setitem__ = ProxyLookup(setitem)
    __delitem__ = ProxyLookup(delitem)
    __len__ = ProxyLookup(len)
    __hash__ = ProxyLookup(hash)
    __repr__ = ProxyLookup(repr)
    __str__ = ProxyLookup(str)
    __bytes__ = ProxyLookup(bytes)
    __iter__ = ProxyLookup(iter)
    __next__ = ProxyLookup(next)
    __copy__ = ProxyLookup(copy.copy)
    __deepcopy__ = ProxyLookup(copy.deepcopy)
    __class__ = ProxyLookup(
        fallback=lambda self: type(self)
    )  # 一般不会用到这个回调,会直接返回代理类的__class__ attr
    __dir__ = ProxyLookup(dir)


_app_context = LocalStack()  # 全局的请求上下文


def app_ctx(name):
    data = _app_context.top
    if data is None:
        raise RuntimeError("没有应用上下文,可能是未执行入栈操作")
    else:
        return getattr(data, name)


state: State = LocalProxy(partial(app_ctx, "state"))
current_rss: Rss = LocalProxy(partial(app_ctx, "rss"))
