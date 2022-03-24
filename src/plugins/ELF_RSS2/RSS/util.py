import asyncio
import functools
import math
from typing import Any, Callable

from nonebot.log import logger


# 异步函数超时结束装饰器
def time_out(time: int) -> Callable[..., Any]:
    def decorate(method: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(method)
        async def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
            try:
                return await asyncio.wait_for(
                    method(self, *args, **kwargs), timeout=time
                )
            except asyncio.TimeoutError:
                logger.error(f"{self.name} 检查更新超时，结束此次任务!")

        return wrapper

    return decorate


def convert_size(size_bytes: int) -> str:
    if size_bytes == 0:
        return "0 B"
    size_name = ("B", "KB", "MB", "GB", "TB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[i])
