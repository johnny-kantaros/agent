import asyncio
import logging
import os

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from src.integrations.telegram.webhook import handle_telegram_update
from src.planner.agent import agent

load_dotenv()
logging.basicConfig(level=logging.INFO)

router = APIRouter()
SECRET_TOKEN = os.environ.get("TELEGRAM_WEBHOOK_SECRET")
if not SECRET_TOKEN:
    raise RuntimeError("TELEGRAM_WEBHOOK_SECRET is not set")


class SendMessageRequest(BaseModel):
    message: str


@router.post("/message/{token}")
def send_message(token: str, data: SendMessageRequest):
    if token != SECRET_TOKEN:
        raise HTTPException(status_code=403, detail="Forbidden")
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
    logging.info(f"Received Telegram update: {data}")

    asyncio.create_task(handle_telegram_update(data))
    return {"ok": True}


@router.get("/health")
def health():
    return {"health": "OK"}
