import json
import logging

from openai import OpenAI
from openai.types.chat import ChatCompletionUserMessageParam

from src.models.interface import AgentUpdate
from src.planner.tool_executor import ToolExecutor
from src.planner.utils import create_system_message
from src.tools.registry import TOOLS

client = OpenAI()
logging.basicConfig(level=logging.INFO)

MAX_STEPS = 4
MAX_HISTORY = 10


def trim_messages(messages):
    system = messages[0]
    rest = messages[1:]
    trimmed = rest[-(MAX_HISTORY - 1) :]

    while trimmed and trimmed[0]["role"] == "tool":
        trimmed = trimmed[1:]

    return [system] + trimmed


class Agent:
    def __init__(self):
        self.messages: list = [create_system_message()]
        self.tool_schemas = [tool.schema() for tool in TOOLS.values()]
        self._sleep = False
        self.tool_executor = ToolExecutor()

    def sleep(self):
        self._sleep = True

    def wakeup(self):
        self._sleep = False

    def reset_history(self):
        self.messages = [create_system_message()]

    async def run_stream(self, query: str):
        if self._sleep:
            yield AgentUpdate(
                type="final", message="Agent sleeping: send /wakeup to wake the agent up"
            )
            return

        self.messages[0] = create_system_message()
        self.messages.append(ChatCompletionUserMessageParam(role="user", content=query))

        for _ in range(MAX_STEPS):
            self.messages = trim_messages(self.messages)

            logging.info("Messages:\n%s", json.dumps(self.messages, indent=2, default=str))

            response = client.chat.completions.create(
                model="gpt-5-mini",
                messages=self.messages,
                tools=self.tool_schemas,
            )
            message = response.choices[0].message

            if message.tool_calls:
                self.messages.append(
                    {
                        "role": "assistant",
                        "content": message.content or "",
                        "tool_calls": message.tool_calls,
                    }
                )

                tool_call = message.tool_calls[0]
                tool_call_id = tool_call.id

                tool_result = None

                async for event in self.tool_executor.run_tool(tool_call):
                    if event.type == "progress":
                        yield AgentUpdate(type="progress", message=event.message)

                    elif event.type == "result":
                        tool_result = event.result

                if tool_result is None:
                    tool_result = {"error": "Tool did not return result"}

                self.messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call_id,
                        "content": json.dumps(tool_result),
                    }
                )

                continue

            # If there are no tool calls, yield final response
            yield await self._process_final_response(message)
            return

        yield AgentUpdate(type="final", message="Sorry, something went wrong.")

    async def _process_final_response(self, message):
        final_text = message.content or ""

        self.messages.append(
            {
                "role": "assistant",
                "content": final_text,
            }
        )

        return AgentUpdate(type="final", message=final_text)


agent = Agent()
