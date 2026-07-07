from collections.abc import AsyncGenerator

from src.models.interface import ToolCallResult, ToolEvent
from src.tools.base import Tool
from src.tools.calendar.calendar_service import calendar_service


class CreateCalendarEvent(Tool):
    name = "create_calendar_event"
    description = "Creates a calendar event."

    parameters = {
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "Title of the calendar event.",
            },
            "start_time": {
                "type": "string",
                "description": "Event start time in ISO 8601 format.",
            },
            "end_time": {
                "type": "string",
                "description": "Event end time in ISO 8601 format.",
            },
            "location": {
                "type": "string",
                "description": "Event location (optional).",
            },
            "description": {
                "type": "string",
                "description": "Additional details about the event.",
            },
            "attendees": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of attendee emails.",
            },
            "timezone": {
                "type": "string",
                "description": "Timezone for the event (e.g. America/Los_Angeles).",
            },
        },
        "required": ["title", "start_time", "end_time"],
    }

    def __init__(self):
        self.service = calendar_service

    async def run(self, tool_input: dict, user_context: dict) -> AsyncGenerator[ToolEvent, None]:

        try:
            yield ToolEvent(type="progress", message="Creating calendar event...")

            title = tool_input.get("title")
            start_time = tool_input.get("start_time")
            end_time = tool_input.get("end_time")

            duration_minutes = tool_input.get("duration_minutes")
            location = tool_input.get("location")
            description = tool_input.get("description")
            attendees = tool_input.get("attendees")

            timezone = (
                user_context.get("timezone") or tool_input.get("timezone") or "America/Los_Angeles"
            )

            if not title:
                yield ToolEvent(
                    type="result",
                    result=ToolCallResult(
                        status="failure",
                        data={"message": "Missing required field: title"},
                    ),
                )
                return

            if not start_time:
                yield ToolEvent(
                    type="result",
                    result=ToolCallResult(
                        status="failure",
                        data={"message": "Missing required field: start_time"},
                    ),
                )
                return

            if not end_time and not duration_minutes:
                yield ToolEvent(
                    type="result",
                    result=ToolCallResult(
                        status="failure",
                        data={"message": "Provide either end_time or duration_minutes"},
                    ),
                )
                return

            event = self.service.create_event(
                title=title,
                start_time=start_time,
                end_time=end_time,
                duration_minutes=duration_minutes,
                location=location,
                description=description,
                attendees=attendees,
                timezone=timezone,
            )

            yield ToolEvent(
                type="result",
                result=ToolCallResult(
                    status="success",
                    data=event,
                ),
            )

        except Exception as e:
            yield ToolEvent(
                type="result",
                result=ToolCallResult(
                    status="failure",
                    data={"error": str(e)},
                ),
            )
