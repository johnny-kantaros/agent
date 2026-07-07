from collections.abc import AsyncGenerator

from src.models.interface import ToolCallResult, ToolEvent
from src.tools.base import Tool
from src.tools.calendar.calendar_service import calendar_service


class FindCalendarTimeSlot(Tool):
    name = "find_calendar_time_slot"
    description = (
        "Find the next available time slot of a given duration within a specified time range. "
        "Returns the suggested start and end times or indicates no slot is available."
    )

    parameters = {
        "type": "object",
        "properties": {
            "duration_minutes": {
                "type": "integer",
                "description": "Length of the desired time slot in minutes.",
            },
            "start_range": {
                "type": "string",
                "description": "Start of the time range to search (ISO 8601).",
            },
            "end_range": {
                "type": "string",
                "description": "End of the time range to search (ISO 8601).",
            },
            "step_minutes": {
                "type": "integer",
                "description": "Increment step in minutes when checking availability (default 15).",
            },
        },
        "required": ["duration_minutes", "start_range", "end_range"],
    }

    def __init__(self):
        self.service = calendar_service

    async def run(self, tool_input: dict, user_context: dict) -> AsyncGenerator[ToolEvent, None]:
        try:
            result = self.service.find_time_slot(
                duration_minutes=tool_input["duration_minutes"],
                start_range=tool_input["start_range"],
                end_range=tool_input["end_range"],
                step_minutes=tool_input.get("step_minutes", 15),
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
