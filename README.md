# Personal Agent

A conversational AI agent that automates personal tasks through a Telegram interface.

## Features

- **Gmail**: Search, read, draft, and manage emails
- **Calendar**: Check availability, find time slots, create and view events
- **Tennis Booking**: Check schedules, initiate and confirm court reservations
- **Squash Booking**: Check Bay Club availability and book courts
- **Flights**: Search for flights
- **Tasks**: Create, update, list, and complete tasks with persistent SQLite storage
- **Telegram**: Webhook-based integration with per-chat session management

## Tech Stack

Python 3.11 • FastAPI • OpenAI GPT-5-mini • SQLite • Google APIs • Fly.io

## Setup

1. Install dependencies:
```bash
uv sync
```

2. Configure environment:
```bash
cp .env.example .env
# Edit .env with your credentials
```

## Running

**Local development:**
```bash
uvicorn src.main:app --reload --port 8000
```

**Deploy to Fly.io:**
```bash
fly deploy
```

## Testing Locally via Postman

1. Create a session:
```
POST /sessions/{token}
→ {"session_id": "..."}
```

2. Send a message:
```
POST /sessions/{session_id}/message/{token}
{"message": "..."}
```

3. Delete a session:
```
DELETE /sessions/{session_id}/{token}
```

## Testing Telegram Locally

1. Expose local server:
```bash
ngrok http 8000
```

2. Set webhook:
```bash
curl -X POST "https://api.telegram.org/bot<BOT_TOKEN>/setWebhook" \
     -d "url=<NGROK_URL>/telegram/webhook/<SECRET_TOKEN>"
```

## Telegram Commands

- `/clear` - Clear chat history for your session
- Natural language queries for all other actions

## Development

**Code quality:**
```bash
ruff check .
ruff format .
mypy src/
```

**Adding new tools:**
1. Create a tool class in `src/tools/` inheriting from `Tool`
2. Implement `run()` and define `parameters`
3. Register in `src/tools/registry.py`
