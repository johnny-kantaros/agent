import logging

from src.integrations.telegram.client import TelegramClient
from src.integrations.telegram.telegram_progress_renderer import TelegramProgressRenderer
from src.models.interface import RequestContext
from src.planner import agent
from src.planner.session import ChatSession

logger = logging.getLogger(__name__)


async def dispatch(ctx: RequestContext, client: TelegramClient, session: ChatSession) -> None:
    renderer = TelegramProgressRenderer(client, ctx.chat_id)
    await client.send_chat_action(ctx.chat_id, "typing")
    await renderer.start()

    finalized = False

    try:
        async for event in agent.run_stream(ctx.text, session):
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
