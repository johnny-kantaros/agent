import asyncio
import time

from src.integrations.telegram.client import TelegramClient


class TelegramProgressRenderer:
    def __init__(self, client: TelegramClient, chat_id: int):
        self.client = client
        self.chat_id = chat_id

        self.message_id: int | None = None
        self.last_text: str = ""
        self.last_edit_ts: float = 0.0

        self.min_interval: float = 0.8  # critical for rate limits
        self.steps: list[str] = []

        self._spinner_task: asyncio.Task | None = None
        self._running: bool = False

    async def start(self):
        msg = await self.client.send_message(self.chat_id, "🤖 Starting...")

        self.message_id = msg["message_id"]
        self._running = True

        self._spinner_task = asyncio.create_task(self._spinner())

    async def _spinner(self):
        dots = 0

        while self._running:
            if self.steps:
                base = self.steps[-1]
                animated = base + "." * (dots % 4)
                await self._edit(animated)

            dots += 1
            await asyncio.sleep(0.5)

    async def update(self, text: str):
        self.steps.append(text)
        await self._edit("\n".join(self.steps[-5:]))

    async def _edit(self, text: str):
        if self.message_id is None:
            return

        now = time.time()

        # dedupe
        if text == self.last_text:
            return

        # throttle
        if now - self.last_edit_ts < self.min_interval:
            return

        await self.client.edit_message(
            self.chat_id,
            self.message_id,
            text,
        )

        self.last_text = text
        self.last_edit_ts = now

    async def finalize(self, text: str):
        self._running = False

        if self._spinner_task:
            self._spinner_task.cancel()

        if self.message_id is None:
            return

        await self.client.edit_message(
            self.chat_id,
            self.message_id,
            text,
        )
