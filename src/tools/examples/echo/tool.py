from src.tools.base import Tool
from src.tools.examples.echo.service import EchoService


class EchoTool(Tool):
    name = "echo"
    description = "Echoes back the exact message provided."

    def __init__(self):
        self.service = EchoService()

    def run(self, tool_input: dict, user_context: dict) -> dict:
        message = tool_input.get("message", "")
        return self.service.echo(message)