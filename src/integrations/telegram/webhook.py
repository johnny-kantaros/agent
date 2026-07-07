import asyncio
import logging
from typing import Any

from src.integrations.telegram.client import TelegramClient
from src.integrations.telegram.dispatch import dispatch
from src.integrations.telegram.validate import advance, extract_context, validate
from src.planner.session import ChatSession

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_CLIENT = TelegramClient()


async def _route_command(ctx, client: TelegramClient, session: ChatSession) -> bool:
    if ctx.text == "/clear":
        session.reset()
        await client.send_message(ctx.chat_id, "Chat history cleared.")
        return True
    return False


async def handle_telegram_update(update: dict[str, Any], session: ChatSession) -> None:
    should_skip, update_id = validate(update)
    if should_skip or update_id is None:
        return

    ctx = extract_context(update)

    if not ctx.text:
        advance(update_id)
        return

    if await _route_command(ctx, TELEGRAM_CLIENT, session):
        advance(update_id)
        return

    asyncio.create_task(dispatch(ctx, TELEGRAM_CLIENT, session))
    advance(update_id)
