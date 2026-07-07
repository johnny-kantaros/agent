import asyncio
import logging

from src.integrations.telegram.client import TelegramClient
from src.integrations.telegram.telegram_progress_renderer import TelegramProgressRenderer
from src.models.interface import RequestContext
from src.planner import agent

logger = logging.getLogger(__name__)

AGENT_LOCK = asyncio.Lock()


async def dispatch(ctx: RequestContext, client: TelegramClient) -> None:
    if AGENT_LOCK.locked():
        await client.send_message(ctx.chat_id, "Still working on the last request...")
        return

    renderer = TelegramProgressRenderer(client, ctx.chat_id)
    await client.send_chat_action(ctx.chat_id, "typing")
    await renderer.start()

    finalized = False

    try:
        async with AGENT_LOCK:
            async for event in agent.run_stream(ctx.text):
                if event.type == "progress":
                    await renderer.update(event.message)

                elif event.type == "final":
                    await renderer.finalize(event.message)
                    finalized = True
                    break

        if not finalized:
            await renderer.finalize("Something went wrong.")

    except Exception as e:
        logger.error(f"Agent error: {e}")
        await renderer.finalize("Something went wrong.")
