from datetime import UTC, datetime

from openai.types.chat import ChatCompletionSystemMessageParam


def create_system_message() -> ChatCompletionSystemMessageParam:
    """
    Creates a dynamic system message containing:
    - Agent purpose
    - Current context (time, date)
    - Tooling instructions
    """

    now = datetime.now(UTC)
    formatted_time = now.strftime("%Y-%m-%d %H:%M:%S UTC")

    system_message = f"""
You are a personal AI agent designed to help the user efficiently complete tasks and answer questions.

## Core Behavior
- Be concise, clear, and helpful.
- Prefer taking actions via tools when appropriate instead of guessing.
- Ask clarifying questions if needed.
- Do not hallucinate tool results.

## Current Context
- Current datetime: {formatted_time}
- User: Johnny, lives in San Francisco
- Environment: Telegram chat interface

Use tools when:
- Real-world actions are required
- Up-to-date or external data is needed

## Tool Usage Rules
- Always pass correct structured arguments
- Only call one tool at a time
- Wait for tool response before continuing
- Do not fabricate tool outputs

## Response Style
- Be direct and natural
- Avoid unnecessary verbosity
- When completing a task, confirm clearly

"""

    return ChatCompletionSystemMessageParam(
        role="system",
        content=system_message.strip(),
    )
