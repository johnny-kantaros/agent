import asyncio
import logging
import os
from typing import Any

from dotenv import load_dotenv

from src.integrations.telegram.client import TelegramClient
from src.integrations.telegram.telegram_progress_renderer import TelegramProgressRenderer
from src.models.interface import RequestContext
from src.planner.agent import Agent, agent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

LAST_UPDATE_ID: int | None = None
AGENT_LOCK = asyncio.Lock()

TELEGRAM_CLIENT = TelegramClient()

user_id_env = os.environ.get("TELEGRAM_USER_ID")
if not user_id_env:
    raise ValueError("TELEGRAM_USER_ID is not set")
ALLOWED_USER_ID: int = int(user_id_env)


def _safe_create_task(coro):
    task = asyncio.create_task(coro)

    def _handle(task):
        try:
            task.result()
        except Exception as e:
            logger.error(f"Background task failed: {e}")

    task.add_done_callback(_handle)


def _get_update_id(update: dict[str, Any]) -> int | None:
    """Safely extracts update_id from a Telegram update."""
    update_id = update.get("update_id")
    if update_id is None:
        logger.warning("Skipping update with no update_id")
        return None
    return int(update_id)


def _validate_update(update: dict[str, Any]) -> tuple[bool, int | None]:
    """Determines whether the Telegram update should be skipped."""
    global LAST_UPDATE_ID

    update_id = _get_update_id(update)
    if update_id is None:
        return True, None

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

    # Ignore messages from bots
    if message.get("from", {}).get("is_bot", False):
        logger.debug(f"Skipping message from bot in update_id={update_id}")
        return True, None

    # Restrict to a single allowed user
    user_id = message.get("from", {}).get("id")
    if user_id != ALLOWED_USER_ID:
        logger.warning(f"Unauthorized user_id={user_id}")
        return True, None

    return False, update_id


def _extract_request_context(update: dict[str, Any]) -> RequestContext:
    message = update["message"]
    chat_id = message["chat"]["id"]
    user_id = message["from"]["id"]
    text = message.get("text", "").strip()

    logger.info(f"user_id={user_id}, chat_id={chat_id}, text='{text}'")

    return RequestContext(
        chat_id=chat_id,
        user_id=user_id,
        text=text,
    )


async def _handle_special_commands(
    ctx: RequestContext, agent: Agent, client: TelegramClient
) -> bool:
    if ctx.text == "/clear":
        agent.reset_history()
        await client.send_message(ctx.chat_id, "Chat history cleared.")
        return True

    if ctx.text == "/sleep":
        agent.sleep()
        await client.send_message(ctx.chat_id, "Agent sleeping.")
        return True

    if ctx.text == "/wakeup":
        agent.wakeup()
        await client.send_message(ctx.chat_id, "Agent activated.")
        return True

    return False


async def handle_telegram_update(update: dict[str, Any]) -> None:
    global LAST_UPDATE_ID

    should_skip, update_id = _validate_update(update)
    if should_skip:
        return

    ctx = _extract_request_context(update)

    if not ctx.text:
        LAST_UPDATE_ID = update_id
        return

    # commands
    if await _handle_special_commands(ctx, agent, TELEGRAM_CLIENT):
        LAST_UPDATE_ID = update_id
        return

    # async execution
    _safe_create_task(handle_message_request(ctx, agent=agent, client=TELEGRAM_CLIENT))

    LAST_UPDATE_ID = update_id


async def handle_message_request(ctx: RequestContext, agent: Agent, client: TelegramClient) -> None:
    renderer = TelegramProgressRenderer(client, ctx.chat_id)

    await client.send_chat_action(ctx.chat_id, "typing")
    await renderer.start()

    finalized = False

    try:
        async with AGENT_LOCK:
            async for event in agent.run_stream(query=ctx.text):
                event_type = event.get("type")
                message = event.get("message", "")

                if event_type == "progress":
                    await renderer.update(message)

                elif event_type == "final":
                    await renderer.finalize(message)
                    finalized = True
                    break

        if not finalized:
            await renderer.finalize("✅ Done")

    except Exception as e:
        logger.error(f"Agent error: {e}")
        await renderer.finalize("❌ Something went wrong.")
