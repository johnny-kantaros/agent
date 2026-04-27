from collections.abc import AsyncGenerator

from src.models.interface import ToolCallResult, ToolEvent
from src.tools.base import Tool
from src.tools.examples.echo.echo_service import EchoService


class EchoTool(Tool):
    name = "echo"
    description = "Echoes back the exact message provided."
    parameters = {
        "type": "object",
        "properties": {"message": {"type": "string", "description": "The message to echo"}},
        "required": ["message"],
    }

    def __init__(self):
        self.service = EchoService()

    async def run(
        self,
        tool_input: dict,
        user_context: dict,
    ) -> AsyncGenerator[ToolEvent, None]:
        message = tool_input.get("message", "")
        yield ToolEvent(
            type="result",
            result=ToolCallResult(
                status="success",
                data={"message": self.service.echo(message)},
            ),
        )
