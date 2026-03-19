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

    chat_id = update["message"]["chat"]["id"]
    text = update["message"].get("text", "")

    # Run your agent
    response = agent.execute(query=text)

    # Respond back to telegram
    send_response_message(chat_id, response.get("response"))
