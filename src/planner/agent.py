import json
import logging

from openai import OpenAI
from openai.types.chat import ChatCompletionUserMessageParam

from src.planner.utils import create_system_message
from src.tools.calendar.check_availability_tool import CheckCalendarAvailability
from src.tools.calendar.create_event_tool import CreateCalendarEvent
from src.tools.calendar.find_timeslot import FindCalendarTimeSlot
from src.tools.calendar.get_calendar_events_tool import GetCalendarEvents
from src.tools.examples.echo.echo_tool import EchoTool
from src.tools.registry import TOOLS, register
from src.tools.tennis.confirm_tennis_court_reservation_tool import TennisCourtConfirmTool
from src.tools.tennis.start_tennis_court_reservation_tool import TennisCourtBookerInitialization
from src.tools.tennis.tennis_schedule_tool import TennisScheduleChecker

client = OpenAI()
logging.basicConfig(level=logging.INFO)

MAX_STEPS = 4
MAX_HISTORY = 10


register(EchoTool())
register(TennisScheduleChecker())
register(TennisCourtBookerInitialization())
register(TennisCourtConfirmTool())
register(CreateCalendarEvent())
register(GetCalendarEvents())
register(FindCalendarTimeSlot())
register(CheckCalendarAvailability())


def trim_messages(messages):
    """
    Trim history without breaking assistant->tool relationships.
    """
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

    def sleep(self):
        self._sleep = True

    def wakeup(self):
        self._sleep = False

    def reset_history(self):
        self.messages = [create_system_message()]

    def execute(self, query: str):
        if self._sleep:
            return {"response": "Agent sleeping: send /wakeup to wake the agent up"}

        self.messages[0] = create_system_message()
        # add user message
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

                for tool_call in message.tool_calls:
                    tool_name = tool_call.function.name
                    tool_call_id = tool_call.id

                    try:
                        args = json.loads(tool_call.function.arguments)
                    except json.JSONDecodeError:
                        args = {}

                    tool_instance = TOOLS.get(tool_name)

                    if not tool_instance:
                        result = {"error": f"Tool '{tool_name}' not found"}
                    else:
                        try:
                            result = tool_instance.run(args, user_context={})
                        except Exception as e:
                            result = {"error": str(e)}

                    self.messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call_id,
                            "content": json.dumps(result),
                        }
                    )

                continue

            self.messages.append({"role": "assistant", "content": message.content or ""})

            return {
                "response": message.content,
                "chat_history": self.messages,
            }

        return {"response": "Sorry, something went wrong."}


agent = Agent()
