from typing import Any

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
            "reminders": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "method": {
                            "type": "string",
                            "enum": ["email", "popup"],
                        },
                        "minutes_before": {
                            "type": "integer",
                            "description": "Minutes before event to trigger reminder.",
                        },
                    },
                    "required": ["method", "minutes_before"],
                },
                "description": "Optional reminders for the event.",
            },
        },
        "required": ["title", "start_time", "end_time"],
    }

    def __init__(self):
        self.service = calendar_service

    async def run(self, tool_input: dict, user_context: dict) -> dict:
        try:
            # Required Fields
            title = tool_input.get("title")
            start_time = tool_input.get("start_time")

            # Optional Fields
            end_time = tool_input.get("end_time")
            duration_minutes = tool_input.get("duration_minutes")
            location = tool_input.get("location")
            description = tool_input.get("description")
            attendees = tool_input.get("attendees")

            # Prefer user context timezone, fallback to input, then default
            timezone = (
                user_context.get("timezone") or tool_input.get("timezone") or "America/Los_Angeles"
            )

            # Basic validation
            if not title:
                return {"status": "error", "message": "Missing required field: title"}

            if not start_time:
                return {"status": "error", "message": "Missing required field: start_time"}

            if not end_time and not duration_minutes:
                return {
                    "status": "error",
                    "message": "Provide either end_time or duration_minutes",
                }

            response: dict[str, Any] = self.service.create_event(
                title=title,
                start_time=start_time,
                end_time=end_time,
                duration_minutes=duration_minutes,
                location=location,
                description=description,
                attendees=attendees,
                timezone=timezone,
            )

            return response

        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
            }
