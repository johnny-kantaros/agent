# Personal Agent

A conversational AI agent that automates personal tasks through a Telegram interface.

## Features

- **Calendar**: Check availability, find time slots, create events, view upcoming items
- **Tennis Booking**: Check schedules, initiate and confirm reservations
- **Squash Booking**: Check Bay Club availability and book courts
- **Tasks**: Create, update, list, search, and complete tasks with persistent storage
- **Telegram Integration**: Interact via Telegram with webhook support
- **Session Management**: Chat history and sleep/wakeup commands

## Tech Stack

Python 3.11 • FastAPI • OpenAI GPT-5-mini • SQLite • Google Calendar API • Fly.io

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

## Testing Telegram Locally

1. Expose local server:
```bash
ngrok http 8000
```

2. Set webhook:
```bash
curl -X POST "https://api.telegram.org/bot<BOT_TOKEN>/setWebhook" \
     -d "url=<NGROK_URL>/telegram/webhook"
```

## Debugging

**View logs:**
```bash
# Local: logs appear in terminal
# Fly.io: fly logs
```

**Access database:**
```bash
sqlite3 /data/agent.db
```

## Telegram Commands

- `/sleep` - Stop responding to queries
- `/wakeup` - Resume responding
- `/reset` - Clear chat history
- Natural language queries for all other actions

## Development

**Code quality:**
```bash
ruff check .
ruff format .
mypy src/
```

**Adding new tools:**
1. Create tool class in `src/tools/` inheriting from `Tool`
2. Implement `run()` and `schema()` methods
3. Register in `src/planner/agent.py`
