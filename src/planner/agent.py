from openai import OpenAI
import json

from openai.types.chat import ChatCompletionUserMessageParam, ChatCompletionSystemMessageParam

from src.tools.examples.echo.echo_tool import EchoTool
from src.tools.registry import TOOLS, register
from src.tools.tennis.confirm_tennis_court_reservation_tool import TennisCourtConfirmTool
from src.tools.tennis.start_tennis_court_reservation_tool import TennisCourtBookerInitialization
from src.tools.tennis.tennis_schedule_tool import TennisScheduleChecker

client = OpenAI()

MAX_STEPS = 6


def run_agent(messages: list, tools: list):
    """
    Simple react style loop that exposes tools added to the registry at build time.
    The reasoner will iteratively call tools until a final synthesis is complete.

    Args:
        messages: conversation history
        tools: tool schemas for the LLM

    Returns: Agent output """

    for _ in range(MAX_STEPS):

        response = client.chat.completions.create(
            model="gpt-5-mini",
            messages=messages,
            tools=tools,
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
            messages.append({
                "role": "assistant",
                "content": message.content or "",
                "tool_calls": message.tool_calls
            })

            # tool response
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call_id,
                "content": json.dumps(result)
            })

        else:
            # final response
            messages.append({
                "role": "assistant",
                "content": message.content or ""
            })

            return message.content or ""

    return "Sorry, something went wrong."


if __name__ == "__main__":

    message1 = "can you book court 1 for lafayette at 9am-10:30am on 3/10?"
    message2 = "today's date and time is 03/04/2026 at 9:35pm"

    register(EchoTool())
    register(TennisScheduleChecker())
    register(TennisCourtBookerInitialization())
    register(TennisCourtConfirmTool())
    tool_schemas = [tool.schema() for tool in TOOLS.values()]

    output = run_agent(
        messages=[
            ChatCompletionUserMessageParam(
                role="user",
                content=message1
            ),
            ChatCompletionSystemMessageParam(
                role="system",
                content=message2
            )
        ],
        tools=tool_schemas
    )

    print(output)