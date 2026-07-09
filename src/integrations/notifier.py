import logging
import os

from src.integrations.telegram.client import TelegramClient
from src.tools.gmail.gmail_service import gmail_service

logger = logging.getLogger(__name__)

_telegram = TelegramClient()
_telegram_user_id = int(os.environ.get("TELEGRAM_USER_ID", "0"))
_notify_email = os.environ.get("NOTIFY_EMAIL")


async def notify(message: str, channels: list[str]) -> None:
    for channel in channels:
        try:
            if channel == "telegram":
                await _telegram.send_message(_telegram_user_id, message)
            elif channel == "email" and _notify_email:
                gmail_service.send_email(
                    to=_notify_email,
                    subject="Agent Job Complete",
                    body=message,
                )
        except Exception as e:
            logger.error(f"Failed to notify via {channel}: {e}")
