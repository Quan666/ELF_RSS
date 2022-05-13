import nonebot
from nonebot.adapters.onebot.v11 import Adapter as OneBotV11Adapter

nonebot.init()
app = nonebot.get_asgi()
driver = nonebot.get_driver()
driver.register_adapter(OneBotV11Adapter)
config = driver.config
nonebot.load_plugins("src/plugins")

if __name__ == "__main__":
    nonebot.run(app="bot:app")
