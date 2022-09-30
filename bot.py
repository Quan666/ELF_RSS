from typing import Optional
import nonebot
from nonebot.adapters.onebot.v11 import Adapter as OneBotV11Adapter

nonebot.init()
app = nonebot.get_asgi()
driver = nonebot.get_driver()
driver.register_adapter(OneBotV11Adapter)
nonebot.load_plugins("src/plugins")


if __name__ == "__main__":
    nonebot.run(app="__mp_main__:app")

    # import asyncio
    # from src.plugins.ELF_RSS2.telegram import bot

    # # async def _():
    # #     print("start nonebot")
    # #     nonebot.run(app="__mp_main__:app")
    # # async def _2():
    # #     print("start tgbot")
    # #     await bot.start(bot_token="1398912644:AAEVZkhVOb6Ae_QYoFvZU7R2Kb_shh3tvk0")
    # # # 并发执行
    # # async def _m():
    # #     await asyncio.gather( _2(),_())
    # # asyncio.get_event_loop().run_until_complete(_m())

    # # import uvicorn
    # # async def main():

    # #     print("start a")
    # #     config = uvicorn.Config("__mp_main__:app", log_level="info")
    # #     server = uvicorn.Server(config)
    # #     await server.serve()
    # # async def _():
    # #     print("start",bot.list_event_handlers())
    # #     await bot.start(bot_token="1398912644:AAEVZkhVOb6Ae_QYoFvZU7R2Kb_shh3tvk0")
    # #     # await bot.run_until_disconnected()
    # #     print("end")

    # # # 并发执行
    # # async def _m():
    # #     await asyncio.gather( main(),_())
    # # asyncio.get_event_loop().run_until_complete(_m())

    # def run(
    #     self,
    #     host: Optional[str] = None,
    #     port: Optional[int] = None,
    #     *,
    #     app: Optional[str] = None,
    #     **kwargs,
    # ):
    #     """使用 `uvicorn` 启动 FastAPI"""
    #     # super().run(host, port, app, **kwargs)
    #     LOGGING_CONFIG = {
    #         "version": 1,
    #         "disable_existing_loggers": False,
    #         "handlers": {
    #             "default": {
    #                 "class": "nonebot.log.LoguruHandler",
    #             },
    #         },
    #         "loggers": {
    #             "uvicorn.error": {"handlers": ["default"], "level": "INFO"},
    #             "uvicorn.access": {
    #                 "handlers": ["default"],
    #                 "level": "INFO",
    #             },
    #         },
    #     }
    #     config = uvicorn.Config(
    #         app or self.server_app,
    #         host=host or str(self.config.host),
    #         port=port or self.config.port,
    #         reload=self.fastapi_config.fastapi_reload,
    #         reload_dirs=self.fastapi_config.fastapi_reload_dirs,
    #         reload_delay=self.fastapi_config.fastapi_reload_delay,
    #         reload_includes=self.fastapi_config.fastapi_reload_includes,
    #         reload_excludes=self.fastapi_config.fastapi_reload_excludes,
    #         log_config=LOGGING_CONFIG,
    #         **kwargs,
    #     )
    #     server = uvicorn.Server(config=config)
    #     return server.serve()

    # import uvicorn
    # async def main():
    #     print("start a")
    #     driver.__class__.run=run
    #     await driver.run(app="__mp_main__:app")
    #     print("end a")

    # async def _():
    #     print("start", bot.list_event_handlers())
    #     from src.plugins.ELF_RSS2.config import config
    #     await bot.start(bot_token=config.telegram_bot_token)
    #     print("end")

    # # 并发执行
    # async def _m():
    #     await asyncio.gather(_(),main())
    # asyncio.get_event_loop().run_until_complete(_m())
