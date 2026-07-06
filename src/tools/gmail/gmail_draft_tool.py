from collections.abc import AsyncGenerator

from src.models.interface import ToolCallResult, ToolEvent
from src.tools.base import Tool
from src.tools.gmail.gmail_service import gmail_service


class GmailDraftTool(Tool):
    name = "gmail_draft"
    description = """
    Create a draft email in Gmail. Does NOT send — always creates a draft for the user to review.
    Optionally can be a reply to an existing thread by providing thread_id.
    """
    progress_indicator_message = "Creating draft..."

    parameters = {
        "type": "object",
        "properties": {
            "to": {
                "type": "string",
                "description": "Recipient email address.",
            },
            "subject": {
                "type": "string",
                "description": "Email subject line.",
            },
            "body": {
                "type": "string",
                "description": "Email body text.",
            },
            "thread_id": {
                "type": "string",
                "description": "Thread ID to reply to an existing conversation. Optional.",
            },
        },
        "required": ["to", "subject", "body"],
    }

    def __init__(self):
        self.service = gmail_service

    async def run(self, tool_input: dict, user_context: dict) -> AsyncGenerator[ToolEvent, None]:
        try:
            result = self.service.create_draft(
                to=tool_input["to"],
                subject=tool_input["subject"],
                body=tool_input["body"],
                thread_id=tool_input.get("thread_id"),
            )
            yield ToolEvent(
                type="result",
                result=ToolCallResult(
                    status="success",
                    data={**result, "message": "Draft created — open Gmail to review and send."},
                ),
            )
        except Exception as e:
            yield ToolEvent(
                type="result",
                result=ToolCallResult(status="failure", data={"error": str(e)}),
            )
