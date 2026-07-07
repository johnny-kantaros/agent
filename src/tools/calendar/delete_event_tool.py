from collections.abc import AsyncGenerator

from src.models.interface import ToolCallResult, ToolEvent
from src.tools.base import Tool
from src.tools.calendar.calendar_service import calendar_service


class DeleteCalendarEvent(Tool):
    name = "delete_calendar_event"
    description = "Permanently delete a calendar event by ID."

    parameters = {
        "type": "object",
        "properties": {
            "event_id": {
                "type": "string",
                "description": "The event ID to delete.",
            },
        },
        "required": ["event_id"],
    }

    def __init__(self):
        self.service = calendar_service

    async def run(self, tool_input: dict, user_context: dict) -> AsyncGenerator[ToolEvent, None]:
        try:
            result = self.service.delete_event(event_id=tool_input["event_id"])

            yield ToolEvent(
                type="result",
                result=ToolCallResult(status="success", data=result),
            )

        except Exception as e:
            yield ToolEvent(
                type="result",
                result=ToolCallResult(status="failure", data={"error": str(e)}),
            )
