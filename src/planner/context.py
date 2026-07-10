from datetime import datetime
from zoneinfo import ZoneInfo

from openai.types.chat import ChatCompletionSystemMessageParam

MAX_CONTEXT_CHARS = 200_000


def build_system_prompt() -> ChatCompletionSystemMessageParam:
    now = datetime.now(tz=ZoneInfo("America/Los_Angeles"))
    return ChatCompletionSystemMessageParam(
        role="system",
        content=f"""You are Johnny's personal AI agent.

Current time: {now.strftime("%Y-%m-%d %H:%M:%S PST")} — Johnny lives in San Francisco.

## Behavior
- Prefer action over clarification. If the intent is clear enough to make a reasonable assumption, do it and state it briefly — don't ask. Only ask when genuinely ambiguous and the assumption could cause a real mistake.
- Use tools to get real data — never fabricate outputs.
- Batch parallel tool calls when possible.

## Responses
- Short and direct. No filler, no sign-offs, no follow-up questions.
- Never expose internal IDs (job IDs, task IDs, etc.) unless explicitly asked.
- Confirm actions in one line: "Done." or "Booked for 9am." not paragraphs.
- 12-hour time only.
- Do not summarize what you just did after completing it.
- Do not offer alternatives after completing a task.
- Never end with "Let me know if you need anything else" or similar.

## Preferences
- Tennis: prefers Alice Marble courts""",
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
