import os

import requests
from dotenv import load_dotenv

from src.planner.agent import agent

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

user_id = os.environ.get("TELEGRAM_USER_ID")
if not user_id:
    raise ValueError("TELEGRAM_USER_ID is not set")

ALLOWED_USER_ID = int(user_id)  # your Telegram ID


def send_response_message(chat_id: int, text: str):
    requests.post(f"{BASE_URL}/sendMessage", json={"chat_id": chat_id, "text": text})


async def handle_telegram_update(update: dict):
    message = update.get("message")
    if not message:
        return

    # Ignore messages from bots
    if message.get("from", {}).get("is_bot", False):
        return

    user_id = message["from"]["id"]
    chat_id = message["chat"]["id"]
    text = message.get("text", "")

    # Restrict to a single allowed user
    if user_id != ALLOWED_USER_ID:
        return

    if text == "/clear":
        agent.reset_history()
        send_response_message(chat_id, "chat history cleared")
        return

    if text == "/sleep":
        agent.sleep()
        send_response_message(chat_id, "agent sleeping")
        return

    if text == "/wakeup":
        agent.wakeup()
        send_response_message(chat_id, "agent activated")
        return

    # Run agent and respond back
    response = agent.execute(query=text)
    send_response_message(chat_id, response.get("response"))
    return
