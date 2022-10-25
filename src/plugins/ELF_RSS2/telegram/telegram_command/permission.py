from telethon import events
from ...config import config


def handle_permission(event: events.CallbackQuery.Event) -> bool:
    """处理权限"""
    if event.sender_id in config.telegram_admin_ids:
        return True
    else:
        return False
