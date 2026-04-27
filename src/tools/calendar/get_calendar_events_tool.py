from collections.abc import AsyncGenerator
from typing import Any

from src.models.interface import ToolCallResult, ToolEvent
from src.tools.base import Tool
from src.tools.calendar.calendar_service import calendar_service


class GetCalendarEvents(Tool):
    name = "get_calendar_events"
    description = """
    Get all calendar events in a given timeframe. If the user provides a timeframe such as 'the next week', 
    check for the next 7 days. If the user asks for "the weekend of x day", assume Friday, Saturday, and Sunday
    closest to whatever day they're referring to.
    """
    progress_indicator_message = "Fetching calendar events..."

    parameters = {
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "Title of the calendar event (optional, used for filtering).",
            },
            "start_time": {
                "type": "string",
                "description": "Start of the time range in ISO 8601 format.",
            },
            "end_time": {
                "type": "string",
                "description": "End of the time range in ISO 8601 format.",
            },
        },
        "required": ["start_time", "end_time"],
    }

    def __init__(self):
        self.service = calendar_service

    async def run(
        self,
        tool_input: dict,
        user_context: dict,
    ) -> AsyncGenerator[ToolEvent, None]:

        try:
            start_time = tool_input.get("start_time")
            end_time = tool_input.get("end_time")
            query = tool_input.get("title")

            if not start_time:
                yield ToolEvent(
                    type="result",
                    result=ToolCallResult(
                        status="failure",
                        data={"message": "Missing required field: start_time"},
                    ),
                )
                return

            if not end_time:
                yield ToolEvent(
                    type="result",
                    result=ToolCallResult(
                        status="failure",
                        data={"message": "Missing required field: end_time"},
                    ),
                )
                return

            events: list[dict[str, Any]] = self.service.list_events(
                time_min=start_time,
                time_max=end_time,
                query=query,
                max_results=100,
            )

            formatted_events = [
                {
                    "title": ev.get("summary"),
                    "start_time": ev["start"].get("dateTime") or ev["start"].get("date"),
                    "end_time": ev["end"].get("dateTime") or ev["end"].get("date"),
                    "location": ev.get("location"),
                    "description": ev.get("description"),
                    "attendees": [a.get("email") for a in ev.get("attendees", [])],
                    "html_link": ev.get("htmlLink"),
                }
                for ev in events
            ]

            yield ToolEvent(
                type="result",
                result=ToolCallResult(
                    status="success",
                    data={"events": formatted_events},
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
