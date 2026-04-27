from collections.abc import AsyncGenerator
from datetime import datetime, timedelta

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
                "description": "Increment step in minutes to check for availability (default 15).",
            },
            "calendar_id": {
                "type": "string",
                "description": "Calendar ID to search (default primary).",
            },
        },
        "required": ["duration_minutes", "start_range", "end_range"],
    }

    def __init__(self):
        self.service = calendar_service

    async def run(self, tool_input: dict, user_context: dict) -> AsyncGenerator[ToolEvent, None]:

        try:
            duration_minutes = tool_input.get("duration_minutes") or 15
            start_range = tool_input.get("start_range")
            end_range = tool_input.get("end_range")
            step_minutes = tool_input.get("step_minutes", 15)
            calendar_id = tool_input.get("calendar_id") or "primary"

            if not isinstance(start_range, str) or not isinstance(end_range, str):
                yield ToolEvent(
                    type="result",
                    result=ToolCallResult(
                        status="failure",
                        data={"error": "Invalid or missing time range"},
                    ),
                )
                return

            start_dt = datetime.fromisoformat(start_range)
            end_dt = datetime.fromisoformat(end_range)
            delta = timedelta(minutes=step_minutes)
            duration = timedelta(minutes=duration_minutes)

            current_start = start_dt
            while current_start + duration <= end_dt:
                current_end = current_start + duration
                availability = self.service.check_availability(
                    start_time=current_start.isoformat(),
                    end_time=current_end.isoformat(),
                    calendar_id=calendar_id,
                )

                if availability.get("available"):
                    yield ToolEvent(
                        type="result",
                        result=ToolCallResult(
                            status="success",
                            data={
                                "available": True,
                                "suggested_start_time": current_start.isoformat(),
                                "suggested_end_time": current_end.isoformat(),
                            },
                        ),
                    )

                current_start += delta

            # ---------------- NO SLOT FOUND ----------------
            yield ToolEvent(
                type="result",
                result=ToolCallResult(
                    status="success",
                    data={
                        "available": False,
                        "message": "No available slot in range",
                    },
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
