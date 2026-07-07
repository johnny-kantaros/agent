import logging
import os
from typing import Any

from src.models.interface import RequestContext

logger = logging.getLogger(__name__)

LAST_UPDATE_ID: int | None = None

user_id_env = os.environ.get("TELEGRAM_USER_ID")
if not user_id_env:
    raise ValueError("TELEGRAM_USER_ID is not set")
ALLOWED_USER_ID: int = int(user_id_env)


def validate(update: dict[str, Any]) -> tuple[bool, int | None]:
    """Returns (should_skip, update_id). Handles dedup and authorization."""
    global LAST_UPDATE_ID

    update_id = update.get("update_id")
    if update_id is None:
        logger.warning("Skipping update with no update_id")
        return True, None
    update_id = int(update_id)

    if LAST_UPDATE_ID is None:
        LAST_UPDATE_ID = update_id - 1
        logger.info(f"Initialized LAST_UPDATE_ID to {LAST_UPDATE_ID}")

    if update_id <= LAST_UPDATE_ID:
        logger.debug(f"Skipping old update_id={update_id} (LAST_UPDATE_ID={LAST_UPDATE_ID})")
        return True, None

    message = update.get("message")
    if not message:
        logger.debug(f"Skipping update_id={update_id} with no message")
        return True, None

    if message.get("from", {}).get("is_bot", False):
        logger.debug(f"Skipping message from bot in update_id={update_id}")
        return True, None

    user_id = message.get("from", {}).get("id")
    if user_id != ALLOWED_USER_ID:
        logger.warning(f"Unauthorized user_id={user_id}")
        return True, None

    return False, update_id


def extract_context(update: dict[str, Any]) -> RequestContext:
    message = update["message"]
    chat_id = message["chat"]["id"]
    user_id = message["from"]["id"]
    text = message.get("text", "").strip()

    logger.info(f"user_id={user_id}, chat_id={chat_id}, text='{text}'")

    return RequestContext(chat_id=chat_id, user_id=user_id, text=text)


def advance(update_id: int) -> None:
    global LAST_UPDATE_ID
    LAST_UPDATE_ID = update_id
