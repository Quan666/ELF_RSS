from pathlib import Path

import nonebot

from .config import Config
# from .plugins import RSSHUB

global_config = nonebot.get_driver().config
plugin_config = Config(**global_config.dict())
# store all subplugins
_sub_plugins = set()
# load sub plugins
_sub_plugins |= nonebot.load_plugins(
    str((Path(__file__).parent / "plugins").resolve()))
