from . import bot
from ..config import config

bot.start(bot_token=config.telegram_bot_token)
bot.run_until_disconnected()
