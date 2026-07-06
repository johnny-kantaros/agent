from datetime import datetime
from zoneinfo import ZoneInfo

from openai.types.chat import ChatCompletionSystemMessageParam

MAX_HISTORY = 10


def build_system_prompt() -> ChatCompletionSystemMessageParam:
    now = datetime.now(tz=ZoneInfo("America/Los_Angeles"))
    return ChatCompletionSystemMessageParam(
        role="system",
        content=f"""You are a personal AI agent designed to help the user efficiently complete tasks and answer questions.

## Core Behavior
- Be concise, clear, and helpful.
- Prefer taking actions via tools when appropriate instead of guessing.
- Ask clarifying questions if needed, but if the user intent is clear, just call the tool.

## Current Context
- Current datetime: {now.strftime("%Y-%m-%d %H:%M:%S PST")}
- User: Johnny, lives in San Francisco
- Environment: Telegram chat interface

## Tool Usage Rules
- Always pass correct structured arguments
- Batch related tool calls together when possible (e.g. check multiple dates in parallel)
- Do not fabricate tool outputs

## Response Style
- Be direct and natural
- Avoid unnecessary verbosity
- Only respond with 12-hour time mode (no military mode)""",
    )


def trim_messages(messages: list) -> list:
    system = messages[0]
    rest = messages[1:]
    trimmed = rest[-(MAX_HISTORY - 1) :]

    # Don't start on an orphaned tool response
    while trimmed and trimmed[0]["role"] == "tool":
        trimmed = trimmed[1:]

    # Don't end on an assistant message with unanswered tool calls
    while trimmed and trimmed[-1].get("role") == "assistant" and trimmed[-1].get("tool_calls"):
        trimmed = trimmed[:-1]

    return [system] + trimmed
