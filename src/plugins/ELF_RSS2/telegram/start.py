from .. import command
from . import bot
import threading

threading.Thread(target=bot.loop.run_forever).start()
