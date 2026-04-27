import logging
import os

import httpx

logger = logging.getLogger(__name__)


class TelegramClient:
    def __init__(self):
        self.bot_token = os.environ["TELEGRAM_BOT_TOKEN"]
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.client = httpx.AsyncClient(timeout=10.0)

    async def send_message(self, chat_id: int, text: str) -> dict:
        try:
            resp = await self.client.post(
                f"{self.base_url}/sendMessage",
                json={"chat_id": chat_id, "text": text},
            )
            resp.raise_for_status()
            return resp.json()["result"]
        except httpx.HTTPError as e:
            logger.error(f"send_message failed: {e}")
            raise

    async def edit_message(self, chat_id: int, message_id: int, text: str) -> None:
        try:
            await self.client.post(
                f"{self.base_url}/editMessageText",
                json={
                    "chat_id": chat_id,
                    "message_id": message_id,
                    "text": text,
                },
            )
        except httpx.HTTPError as e:
            logger.debug(f"edit_message skipped: {e}")

    async def send_chat_action(self, chat_id: int, action: str = "typing") -> None:
        try:
            await self.client.post(
                f"{self.base_url}/sendChatAction",
                json={"chat_id": chat_id, "action": action},
            )
        except httpx.HTTPError as e:
            logger.debug(f"chat_action failed: {e}")

    async def close(self):
        await self.client.aclose()
