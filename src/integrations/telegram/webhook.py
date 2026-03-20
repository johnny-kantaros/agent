import asyncio
import logging
import os
from typing import Any, TypedDict

import httpx
from dotenv import load_dotenv

from src.planner.agent import Agent, agent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()


class MessageData(TypedDict):
    chat_id: int
    user_id: int
    text: str


BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
if not BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN is not set in environment variables.")

BASE_URL: str = f"https://api.telegram.org/bot{BOT_TOKEN}"
LAST_UPDATE_ID: int | None = None
AGENT_LOCK = asyncio.Lock()

user_id_env = os.environ.get("TELEGRAM_USER_ID")
if not user_id_env:
    raise ValueError("TELEGRAM_USER_ID is not set")
ALLOWED_USER_ID: int = int(user_id_env)


async def send_response_message(chat_id: int, text: str) -> None:
    """
    Sends a text message to a Telegram chat.
    """
    logger.info(f"Sending message to chat_id={chat_id}: {text}")
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                f"{BASE_URL}/sendMessage", json={"chat_id": chat_id, "text": text}
            )
            resp.raise_for_status()
        except httpx.HTTPError as e:
            logger.error(f"Failed to send message to chat_id={chat_id}: {e}")


def _get_update_id(update: dict[str, Any]) -> int | None:
    """
    Safely extracts update_id from a Telegram update.
    """
    update_id = update.get("update_id")
    if update_id is None:
        logger.warning("Skipping update with no update_id")
        return None
    return int(update_id)


def _validate_update(update: dict[str, Any]) -> tuple[bool, int | None]:
    """
    Determines whether the Telegram update should be skipped.
    """
    global LAST_UPDATE_ID

    update_id = _get_update_id(update)
    if update_id is None:
        return True, None

    if LAST_UPDATE_ID is None:
        # Initialize last update ID if first run
        LAST_UPDATE_ID = update_id - 1
        logger.info(f"Initialized LAST_UPDATE_ID to {LAST_UPDATE_ID}")

    if update_id <= LAST_UPDATE_ID:
        logger.debug(f"Skipping old update_id={update_id} (LAST_UPDATE_ID={LAST_UPDATE_ID})")
        return True, None

    message = update.get("message")
    if not message:
        logger.debug(f"Skipping update_id={update_id} with no message")
        return True, None

    # Ignore messages from bots
    if message.get("from", {}).get("is_bot", False):
        logger.debug(f"Skipping message from bot in update_id={update_id}")
        return True, None

    # Restrict to a single allowed user
    user_id = message.get("from", {}).get("id")
    if user_id != ALLOWED_USER_ID:
        logger.warning(f"Unauthorized user_id={user_id} in update_id={update_id}")
        return True, None

    return False, update_id


def _extract_message_data(update: dict[str, Any]) -> MessageData:
    """
    Extracts essential data from a Telegram message.
    """
    message = update["message"]
    chat_id = message["chat"]["id"]
    user_id = message["from"]["id"]
    text = message.get("text", "").strip()

    logger.info(f"Extracted message from user_id={user_id}, chat_id={chat_id}, text='{text}'")
    return {"chat_id": chat_id, "user_id": user_id, "text": text}


async def _handle_special_commands(text: str, agent: Agent, chat_id: int) -> bool:
    """
    Handles Telegram commands: /clear, /sleep, /wakeup.
    """
    if text == "/clear":
        agent.reset_history()
        logger.info(f"Cleared agent history for chat_id={chat_id}")
        await send_response_message(chat_id, "Chat history cleared.")
        return True
    if text == "/sleep":
        agent.sleep()
        logger.info(f"Agent put to sleep for chat_id={chat_id}")
        await send_response_message(chat_id, "Agent sleeping.")
        return True
    if text == "/wakeup":
        agent.wakeup()
        logger.info(f"Agent woken up for chat_id={chat_id}")
        await send_response_message(chat_id, "Agent activated.")
        return True
    return False


async def handle_telegram_update(update: dict[str, Any]) -> None:
    """
    Processes a single Telegram update.
    """
    global LAST_UPDATE_ID

    should_skip_update, update_id = _validate_update(update)
    if should_skip_update:
        return

    msg_data = _extract_message_data(update)
    chat_id = msg_data["chat_id"]
    text = msg_data["text"]

    if not text:
        logger.debug(f"No text to process in update_id={update_id}")
        LAST_UPDATE_ID = update_id
        return

    # Handle commands first
    if await _handle_special_commands(text, agent, chat_id):
        LAST_UPDATE_ID = update_id
        return

    # Normal message processing
    logger.info(f"Processing normal message for chat_id={chat_id}: {text}")
    async with AGENT_LOCK:
        try:
            response = agent.execute(query=text)
            reply_text = response.get("response", "No response from agent.")
            logger.info(f"Agent response for chat_id={chat_id}: {reply_text}")
            await send_response_message(chat_id, reply_text)
        except Exception as e:
            logger.error(f"Error processing agent response for chat_id={chat_id}: {e}")

    # Update last processed ID
    LAST_UPDATE_ID = update_id
    logger.debug(f"Updated LAST_UPDATE_ID={LAST_UPDATE_ID}")
