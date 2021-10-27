import asyncio
import functools

from nonebot import logger


# 异步函数超时结束装饰器
def time_out(time: int):
    def decorate(method):
        @functools.wraps(method)
        async def wrapper(self, *args, **kwargs):
            try:
                return await asyncio.wait_for(
                    method(self, *args, **kwargs), timeout=time
                )
            except asyncio.TimeoutError as te:
                logger.error(f"{self.name} 检查更新超时，结束此次任务!{te}")

        return wrapper

    return decorate
