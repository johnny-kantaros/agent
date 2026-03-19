import json

from openai import OpenAI
from openai.types.chat import ChatCompletionSystemMessageParam, ChatCompletionUserMessageParam

from src.tools.examples.echo.echo_tool import EchoTool
from src.tools.registry import TOOLS, register
from src.tools.tennis.confirm_tennis_court_reservation_tool import TennisCourtConfirmTool
from src.tools.tennis.start_tennis_court_reservation_tool import TennisCourtBookerInitialization
from src.tools.tennis.tennis_schedule_tool import TennisScheduleChecker

client = OpenAI()

MAX_STEPS = 4

register(EchoTool())
register(TennisScheduleChecker())
register(TennisCourtBookerInitialization())
register(TennisCourtConfirmTool())


class Agent:
    def __init__(self):
        self.system_message = "today's date and time is 03/11/2026 at 4pm"
        self.messages: list = [
            ChatCompletionSystemMessageParam(role="system", content=self.system_message)
        ]

        self.tool_schemas = [tool.schema() for tool in TOOLS.values()]
        self._sleep = False

    def sleep(self):
        self._sleep = True

    def wakeup(self):
        self._sleep = False

    def reset_history(self):
        """Clears chat history but keeps system message and tools."""
        self.messages = [
            ChatCompletionSystemMessageParam(role="system", content=self.system_message)
        ]

    def execute(self, query: str):
        """
        Simple react style loop that exposes tools added to the registry at build time.
        The reasoner will iteratively call tools until a final synthesis is complete.

        Args:
            query: incoming query

        Returns: Agent output"""

        if self._sleep:
            return {"response": "Agent sleeping: send /wakeup to wake the agent up"}

        user_message = ChatCompletionUserMessageParam(role="user", content=query)

        self.messages.append(user_message)

        for _ in range(MAX_STEPS):
            response = client.chat.completions.create(
                model="gpt-5-mini",
                messages=self.messages,
                tools=self.tool_schemas,
            )

            message = response.choices[0].message

            # Tool call
            if message.tool_calls:
                tool_call = message.tool_calls[0]
                tool_name = tool_call.function.name
                tool_call_id = tool_call.id

                args = json.loads(tool_call.function.arguments)

                tool_instance = TOOLS[tool_name]
                result = tool_instance.run(args, user_context={})

                # assistant message
                self.messages.append(
                    {
                        "role": "assistant",
                        "content": message.content or "",
                        "tool_calls": message.tool_calls,
                    }
                )

                # tool response
                self.messages.append(
                    {"role": "tool", "tool_call_id": tool_call_id, "content": json.dumps(result)}
                )

            else:
                # final response
                self.messages.append({"role": "assistant", "content": message.content or ""})

                return {"response": message.content, "chat_history": self.messages}

        return {"response": "Sorry, something went wrong."}


agent = Agent()  # Global
