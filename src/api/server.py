import asyncio
import logging
import os

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from src.integrations.telegram.webhook import handle_telegram_update
from src.planner import agent
from src.planner.session import SessionStore

load_dotenv()
logging.basicConfig(level=logging.INFO)

router = APIRouter()
SECRET_TOKEN = os.environ.get("TELEGRAM_WEBHOOK_SECRET")
if not SECRET_TOKEN:
    raise RuntimeError("TELEGRAM_WEBHOOK_SECRET is not set")

session_store = SessionStore()


class SendMessageRequest(BaseModel):
    message: str


@router.post("/sessions/{token}")
def create_session(token: str):
    if token != SECRET_TOKEN:
        raise HTTPException(status_code=403, detail="Forbidden")
    session_id, _ = session_store.create()
    return {"session_id": session_id}


@router.delete("/sessions/{session_id}/{token}")
def delete_session(session_id: str, token: str):
    if token != SECRET_TOKEN:
        raise HTTPException(status_code=403, detail="Forbidden")
    if session_store.get(session_id) is None:
        raise HTTPException(status_code=404, detail="Session not found")
    session_store.delete(session_id)
    return {"status": "deleted"}


@router.post("/sessions/{session_id}/message/{token}")
async def send_message(session_id: str, token: str, data: SendMessageRequest):
    if token != SECRET_TOKEN:
        raise HTTPException(status_code=403, detail="Forbidden")
    session = session_store.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    async for event in agent.run_stream(data.message, session):
        if event.type == "final":
            return {"response": event.message}
    return {}


@router.post("/telegram/webhook/{token}")
async def telegram_webhook(token: str, req: Request):
    if token != SECRET_TOKEN:
        raise HTTPException(status_code=403, detail="Forbidden")

    data = await req.json()
    logging.info(f"Received Telegram update: {data}")

    chat_id = data.get("message", {}).get("chat", {}).get("id")
    if chat_id is None:
        return {"ok": True}

    session = session_store.get_or_create(str(chat_id))
    asyncio.create_task(handle_telegram_update(data, session))
    return {"ok": True}


@router.get("/health")
def health():
    return {"health": "OK"}
