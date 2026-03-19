import os

import requests

from src.planner.agent import agent

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"


def send_response_message(chat_id: int, text: str):
    requests.post(f"{BASE_URL}/sendMessage", json={"chat_id": chat_id, "text": text})


async def handle_telegram_update(update: dict):
    if "message" not in update:
        return

    message = update["message"]
    chat_id = message["chat"]["id"]

    # Ignore messages from bots (including own)
    sender = message.get("from", {})
    if sender.get("is_bot"):
        return

    text = message.get("text", "")

    if text == "/clear":
        agent.reset_history()
        send_response_message(chat_id, "chat history cleared")

    # Run your agent
    response = agent.execute(query=text)

    # Respond back to Telegram
    send_response_message(chat_id, response.get("response"))
