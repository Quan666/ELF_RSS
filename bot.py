#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import nonebot
from nonebot.adapters.onebot.v11 import Adapter as OneBotV11Adapter

# Custom your logger
#
# from nonebot.log import logger, default_format
# logger.add("error.log",
#            rotation="00:00",
#            diagnose=False,
#            level="ERROR",
#            format=default_format)

# You can pass some keyword args config to init function
nonebot.init()
app = nonebot.get_asgi()
driver = nonebot.get_driver()
driver.register_adapter(OneBotV11Adapter)
config = driver.config
nonebot.load_plugins("src/plugins")

# Modify some config / config depends on loaded configs
#
# config = nonebot.get_driver().config
# do something...

# https://v2.nonebot.dev/guide/basic-configuration.html
if __name__ == "__main__":
    nonebot.run(app="bot:app")
