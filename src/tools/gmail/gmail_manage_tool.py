from collections.abc import AsyncGenerator

from src.models.interface import ToolCallResult, ToolEvent
from src.tools.base import Tool
from src.tools.gmail.gmail_service import gmail_service

ACTIONS = ["mark_read", "mark_unread", "archive", "trash", "add_label"]


class GmailManageTool(Tool):
    name = "gmail_manage"
    description = """
    Manage Gmail messages — mark as read/unread, archive, trash, or add a label.
    Requires the message_id from a gmail_search result.
    Use 'trash' carefully — it moves email to trash (recoverable for 30 days).
    """
    progress_indicator_message = "Updating email..."

    parameters = {
        "type": "object",
        "properties": {
            "message_id": {
                "type": "string",
                "description": "The Gmail message ID from a search result.",
            },
            "action": {
                "type": "string",
                "enum": ACTIONS,
                "description": "Action to perform on the message.",
            },
            "label_name": {
                "type": "string",
                "description": "Label name to apply. Required only when action is 'add_label'.",
            },
        },
        "required": ["message_id", "action"],
    }

    def __init__(self):
        self.service = gmail_service

    async def run(self, tool_input: dict, user_context: dict) -> AsyncGenerator[ToolEvent, None]:
        try:
            message_id = tool_input["message_id"]
            action = tool_input["action"]

            if action == "mark_read":
                self.service.mark_read(message_id)
            elif action == "mark_unread":
                self.service.mark_unread(message_id)
            elif action == "archive":
                self.service.archive(message_id)
            elif action == "trash":
                self.service.trash(message_id)
            elif action == "add_label":
                label = tool_input.get("label_name")
                if not label:
                    yield ToolEvent(
                        type="result",
                        result=ToolCallResult(
                            status="failure",
                            data={"message": "label_name required for add_label action"},
                        ),
                    )
                    return
                self.service.add_label(message_id, label)

            yield ToolEvent(
                type="result",
                result=ToolCallResult(
                    status="success", data={"message_id": message_id, "action": action}
                ),
            )
        except Exception as e:
            yield ToolEvent(
                type="result",
                result=ToolCallResult(status="failure", data={"error": str(e)}),
            )
