from src.tools.base import Tool
from src.tools.examples.echo.echo_service import EchoService


class EchoTool(Tool):
    name = "echo"
    description = "Echoes back the exact message provided."
    parameters = {
        "type": "object",
        "properties": {
            "message": {
                "type": "string",
                "description": "The message to echo"
            }
        },
        "required": ["message"]
    }


    def __init__(self):
        self.service = EchoService()

    def run(self, tool_input: dict, user_context: dict) -> dict:
        message = tool_input.get("message", "")
        return {
            "message": self.service.echo(message)
        }