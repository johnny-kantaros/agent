from src.tools.base import Tool
from src.tools.tennis.tennis_service import TennisService
from src.utils.constants import COURTS


class TennisScheduleChecker(Tool):
    name = "tennis_schedule_checker"
    description = "Checks the schedule of one or more tennis courts."

    # Expose allowed court names to the LLM
    ALLOWED_COURTS = list(COURTS.keys())

    parameters = {
        "type": "object",
        "properties": {
            "courts": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": ALLOWED_COURTS
                },
                "description": (
                    "List of court names to check. LLM can only call courts in the allowed list."
                )
            },
            "days": {
                "type": "integer",
                "description": "Number of days ahead to check (default: 7).",
                "default": 7
            },
            "after_hour": {
                "type": "number",
                "description": "Only include slots after this hour (default: 0).",
                "default": 0
            },
            "before_hour": {
                "type": "number",
                "description": "Only include slots before this hour (default: 24).",
                "default": 24
            },
        },
        "required": []
    }

    def __init__(self):
        self.service = TennisService()

    def run(self, tool_input: dict, user_context: dict) -> dict:
        courts = tool_input.get("courts") or ["all"]  # default to all if none
        days = tool_input.get("days", 7)
        after_hour = tool_input.get("after_hour", 0)
        before_hour = tool_input.get("before_hour", 24)

        availability = self.service.check_availability(
            courts=courts,
            days=days,
            after_hour=after_hour,
            before_hour=before_hour
        )

        return {"availability": availability}