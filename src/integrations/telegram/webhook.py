import asyncio
import logging
from typing import Any

from src.integrations.telegram.client import TelegramClient
from src.integrations.telegram.dispatch import dispatch
from src.integrations.telegram.validate import advance, extract_context, validate
from src.planner import agent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_CLIENT = TelegramClient()


def _safe_create_task(coro) -> None:
    task = asyncio.create_task(coro)

    def _handle(t):
        try:
            t.result()
        except Exception as e:
            logger.error(f"Background task failed: {e}")

    task.add_done_callback(_handle)


async def _route_command(ctx, client: TelegramClient) -> bool:
    if ctx.text == "/clear":
        agent.reset_history()
        await client.send_message(ctx.chat_id, "Chat history cleared.")
        return True
    return False


async def handle_telegram_update(update: dict[str, Any]) -> None:
    should_skip, update_id = validate(update)
    if should_skip or update_id is None:
        return

    ctx = extract_context(update)

    if not ctx.text:
        advance(update_id)
        return

    if await _route_command(ctx, TELEGRAM_CLIENT):
        advance(update_id)
        return

    _safe_create_task(dispatch(ctx, TELEGRAM_CLIENT))
    advance(update_id)
