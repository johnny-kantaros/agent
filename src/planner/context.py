from datetime import datetime
from zoneinfo import ZoneInfo

from openai.types.chat import ChatCompletionSystemMessageParam

MAX_CONTEXT_CHARS = 200_000


def build_system_prompt() -> ChatCompletionSystemMessageParam:
    now = datetime.now(tz=ZoneInfo("America/Los_Angeles"))
    return ChatCompletionSystemMessageParam(
        role="system",
        content=f"""You are a personal AI agent designed to help the user efficiently complete tasks and answer questions.

## Core Behavior
- Be concise, clear, and helpful.
- Prefer taking actions via tools when appropriate instead of guessing.
- Don't make things up, but make reasonable assumptions when intent is clear rather than asking for clarification.

## Current Context
- Current datetime: {now.strftime("%Y-%m-%d %H:%M:%S PST")}
- User: Johnny, lives in San Francisco
- Environment: Telegram chat interface

## Tool Usage Rules
- Always pass correct structured arguments
- Batch related tool calls together when possible (e.g. check multiple dates in parallel)
- Do not fabricate tool outputs

## Response Style
- Be direct and concise
- Avoid unnecessary verbosity
- Only respond with 12-hour time mode (no military mode)""",
    )


def build_job_system_prompt() -> ChatCompletionSystemMessageParam:
    return ChatCompletionSystemMessageParam(
        role="system",
        content="""You are running in autonomous job mode. A scheduled task has triggered this session.

## Autonomous Behavior Rules
- Execute the task immediately and completely — do not ask clarifying questions.
- If information is missing, make a reasonable assumption, state it clearly in your response, and proceed.
- Never ask "do you want this as one-time or recurring?" or similar — that was decided when the job was scheduled.
- Respond with a concise summary of what you did, not questions.""",
    )


def _context_size(messages: list) -> int:
    total = 0
    for m in messages:
        total += len(str(m.get("content") or ""))
        if m.get("tool_calls"):
            total += len(str(m["tool_calls"]))
    return total


def trim_messages(messages: list) -> list:
    """Trim history to fit within MAX_CONTEXT_CHARS while preserving coherence.

    Guarantees:
    - System prompt is always first.
    - The most recent user turn and everything after it are never dropped.
    - History always starts at a user message (no orphaned tool/assistant fragments).
    - History never ends on an assistant message with unanswered tool calls.
    """
    system = messages[0]
    rest = list(messages[1:])

    last_user = max((i for i, m in enumerate(rest) if m.get("role") == "user"), default=0)

    while _context_size([system] + rest) > MAX_CONTEXT_CHARS and last_user > 0:
        rest = rest[1:]
        last_user -= 1

    while rest and rest[0].get("role") != "user":
        rest = rest[1:]

    while rest and rest[-1].get("role") == "assistant" and rest[-1].get("tool_calls"):
        rest = rest[:-1]

    return [system] + rest
