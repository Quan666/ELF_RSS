from nonebot.adapters import Bot
from nonebot.permission import Permission
from nonebot_plugin_guild_patch import GuildMessageEvent


class GuildSuperUser:
    async def __call__(self, bot: Bot, event: GuildMessageEvent) -> bool:
        return (
            bot.config.guild_superusers is not None
            and event.get_type() == "message"
            and (
                f"{bot.adapter.get_name().split(maxsplit=1)[0].lower()}:{event.get_user_id()}"
                in bot.config.guild_superusers
                or event.get_user_id() in bot.config.guild_superusers
            )
        )


GUILD_SUPERUSER = Permission(GuildSuperUser())
"""
- **说明**: 匹配任意频道超级用户消息类型事件
"""
