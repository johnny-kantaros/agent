from collections.abc import AsyncGenerator

from src.models.interface import ToolCallResult, ToolEvent
from src.tools.base import Tool
from src.tools.calendar.calendar_service import calendar_service


class UpdateCalendarEvent(Tool):
    name = "update_calendar_event"
    description = "Update an existing calendar event. Only provided fields are changed."

    parameters = {
        "type": "object",
        "properties": {
            "event_id": {
                "type": "string",
                "description": "The event ID to update.",
            },
            "title": {
                "type": "string",
                "description": "New title for the event.",
            },
            "start_time": {
                "type": "string",
                "description": "New start time in ISO 8601 format.",
            },
            "end_time": {
                "type": "string",
                "description": "New end time in ISO 8601 format.",
            },
            "location": {
                "type": "string",
                "description": "New location for the event.",
            },
            "description": {
                "type": "string",
                "description": "New description for the event.",
            },
            "attendees": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Replacement list of attendee emails.",
            },
            "timezone": {
                "type": "string",
                "description": "Timezone for any updated times (e.g. America/Los_Angeles).",
            },
        },
        "required": ["event_id"],
    }

    def __init__(self):
        self.service = calendar_service

    async def run(self, tool_input: dict, user_context: dict) -> AsyncGenerator[ToolEvent, None]:
        try:
            result = self.service.update_event(
                event_id=tool_input["event_id"],
                title=tool_input.get("title"),
                start_time=tool_input.get("start_time"),
                end_time=tool_input.get("end_time"),
                location=tool_input.get("location"),
                description=tool_input.get("description"),
                attendees=tool_input.get("attendees"),
                timezone=tool_input.get("timezone", "America/Los_Angeles"),
            )

            yield ToolEvent(
                type="result",
                result=ToolCallResult(status="success", data=result),
            )

        except Exception as e:
            yield ToolEvent(
                type="result",
                result=ToolCallResult(status="failure", data={"error": str(e)}),
            )
