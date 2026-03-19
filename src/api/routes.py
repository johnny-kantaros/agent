from fastapi import APIRouter, Request
from pydantic import BaseModel

from src.integrations.telegram.webhook import handle_telegram_update
from src.planner.agent import agent

router = APIRouter()


class SendMessageRequest(BaseModel):
    message: str


@router.post("/message")
def send_message(data: SendMessageRequest):
    response = agent.execute(data.message)
    return {"response": response}


# --- Telegram webhook ---
@router.post("/telegram/webhook")
async def telegram_webhook(req: Request):
    """
    Receives updates from Telegram and sends them to the agent.
    """
    data = await req.json()
    await handle_telegram_update(data)
    return {"ok": True}


@router.get("/health")
def health():
    return {"health": "OK"}
