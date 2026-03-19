import os

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from src.integrations.telegram.webhook import handle_telegram_update
from src.planner.agent import agent

load_dotenv()

router = APIRouter()
SECRET_TOKEN = os.environ.get("TELEGRAM_WEBHOOK_SECRET", "change-me")


class SendMessageRequest(BaseModel):
    message: str


@router.post("/message")
def send_message(data: SendMessageRequest):
    response = agent.execute(data.message)
    return {"response": response}


# --- Telegram webhook ---
@router.post("/telegram/webhook/{token}")
async def telegram_webhook(token: str, req: Request):
    """
    Receives updates from Telegram and sends them to the agent.
    """
    if token != SECRET_TOKEN:
        raise HTTPException(status_code=403, detail="Forbidden")

    data = await req.json()
    await handle_telegram_update(data)
    return {"ok": True}


@router.get("/health")
def health():
    return {"health": "OK"}
