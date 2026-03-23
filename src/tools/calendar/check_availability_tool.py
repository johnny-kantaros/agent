from src.tools.base import Tool
from src.tools.calendar.calendar_service import calendar_service


class CheckCalendarAvailability(Tool):
    name = "check_calendar_availability"
    description = """
        Check if a specific time range is free on the calendar. 
        Returns whether the slot is available and any conflicting events.
        If the user does not provide an explicit end time, assume 1 hour.
        If the user asks for "the weekend of x day", assume Friday, Saturday, and Sunday
        closest to whatever day they're referring to.
        """

    parameters = {
        "type": "object",
        "properties": {
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

    def run(self, tool_input: dict, user_context: dict) -> dict:
        try:
            start_time = tool_input.get("start_time")
            end_time = tool_input.get("end_time")

            if not start_time:
                return {"status": "error", "message": "Missing required field: start_time"}
            if not end_time:
                return {"status": "error", "message": "Missing required field: end_time"}

            # Call service to check availability
            availability = self.service.check_availability(
                start_time=start_time,
                end_time=end_time,
            )

            # Format conflicting events if any
            conflicts = []
            if not availability.get("available"):
                for ev in availability.get("conflicts", []):
                    conflicts.append(
                        {
                            "title": ev.get("title"),
                            "start_time": ev.get("start"),
                            "end_time": ev.get("end"),
                        }
                    )

            return {
                "status": "success",
                "available": availability.get("available"),
                "conflicts": conflicts,
            }

        except Exception as e:
            return {"status": "error", "message": str(e)}
