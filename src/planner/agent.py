import asyncio
import json
import logging
from dataclasses import asdict

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionUserMessageParam

from src.models.interface import AgentUpdate, ToolCallResult
from src.planner.context import build_system_prompt, trim_messages
from src.planner.session import ChatSession
from src.tools.registry import TOOLS

client = AsyncOpenAI()
logging.basicConfig(level=logging.INFO)

MAX_STEPS = 50

_tool_schemas = [tool.schema() for tool in TOOLS.values()]


async def _run_tool(tool_call) -> ToolCallResult:
    tool_name = tool_call.function.name

    try:
        args = json.loads(tool_call.function.arguments)
    except json.JSONDecodeError:
        args = {}

    tool = TOOLS.get(tool_name)

    if not tool:
        return ToolCallResult(status="failure", data={"message": "Tool does not exist"})

    args.pop("_status", None)

    async for event in tool.run(args, user_context={}):
        if event.type == "result" and event.result:
            return event.result

    return ToolCallResult(status="failure", data={"message": "Tool did not return a result"})


async def _execute_tool_calls(tool_calls):
    for tc in tool_calls:
        try:
            if status := json.loads(tc.function.arguments).get("_status"):
                yield AgentUpdate(type="progress", message=status)
        except json.JSONDecodeError:
            pass

    async def collect(tc):
        return tc.id, await _run_tool(tc)

    for tool_call_id, result in await asyncio.gather(*[collect(tc) for tc in tool_calls]):
        yield tool_call_id, result


async def run_stream(query: str, session: ChatSession):
    async with session.lock:
        session.messages[0] = build_system_prompt()
        session.messages.append(ChatCompletionUserMessageParam(role="user", content=query))

        for _ in range(MAX_STEPS):
            session.messages = trim_messages(session.messages)

            logging.info("Messages:\n%s", json.dumps(session.messages, indent=2, default=str))

            response = await client.chat.completions.create(
                model="gpt-5-mini",
                messages=session.messages,
                tools=_tool_schemas,
            )
            message = response.choices[0].message

            if message.tool_calls:
                session.messages.append(
                    {
                        "role": "assistant",
                        "content": message.content or "",
                        "tool_calls": message.tool_calls,
                    }
                )

                async for event in _execute_tool_calls(message.tool_calls):
                    if isinstance(event, AgentUpdate):
                        yield event
                    else:
                        tool_call_id, tool_result = event
                        session.messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_call_id,
                                "content": json.dumps(asdict(tool_result)),
                            }
                        )

                continue

            session.messages.append({"role": "assistant", "content": message.content or ""})
            yield AgentUpdate(type="final", message=message.content or "")
            return

        yield AgentUpdate(type="final", message="Sorry, something went wrong.")
