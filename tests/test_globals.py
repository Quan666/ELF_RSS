import unittest
import os
import bot 
from src.plugins.ELF_RSS2.globals import (
    Local,
    LocalProxy,
    LocalStack,
    RequestContext,
    state,
)


class TestGlobals(unittest.TestCase):
    def setUp(self) -> None:
        print("测试开始")

    def test_globals(self):
        import asyncio
        from random import randint

        class Request:
            def __init__(self) -> None:
                self.url = "google.com"
                self.task = "0"

        async def inner(task_id: str):
            await asyncio.sleep(randint(1, 5))
            state.sn = f"{str(state.sn)} inner修改-{task_id}"
            print(f"任务{task_id} inner修改后, state值:{state.sn}")

        async def modify(task_id: str):
            print(f"开始处理任务:{task_id}")
            ctx = RequestContext('rss')
            ctx.push()
            print(f"任务{task_id}初始state:{state.sn}")
            local = Local()
            local.request = Request()
            request_task = local('request')
            request_task.task = request_task.task + '-' + task_id
            
            await asyncio.sleep(randint(1, 5))  # 随机等待1-3秒,达到随机修改顺序的目的
            state.sn = str(state.sn) + "-" + task_id
            await inner(task_id=task_id)
            print(f"任务{task_id} inner修改后, state值:{state.sn}")
            return (state.sn, request_task.task)

        async def run():

            tasks = []
            for i in range(10, 20):
                tasks.append(asyncio.ensure_future(modify(str(i))))
            result = await asyncio.gather(*tasks)
            print("".center(50, "="))
            print(f"协程返回值: {result}")

        loop = asyncio.get_event_loop()
        loop.run_until_complete(run())


if __name__ == "__main__":
    suite = unittest.TestSuite()
    suite.addTest(TestGlobals("test_globals"))

    runner = unittest.TextTestRunner()
    runner.run(suite)
