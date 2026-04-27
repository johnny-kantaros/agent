from collections.abc import AsyncGenerator

from src.models.interface import ToolCallResult, ToolEvent
from src.tools.base import Tool
from src.tools.squash.squash_service import squash_service


class SquashCourtChecker(Tool):
    name = "squash_court_checker"
    description = "Checks available squash courts for a given date and optional time range"
    progress_indicator_message = "Checking squash availability..."

    parameters = {
        "type": "object",
        "properties": {
            "date": {
                "type": "string",
                "description": "Date to check in YYYY-MM-DD format",
            },
            "after_hour": {
                "type": "number",
                "description": "Only include slots after this hour (0-23). Default is 0.",
                "default": 0,
            },
            "before_hour": {
                "type": "number",
                "description": "Only include slots before this hour (0-24). Default is 24.",
                "default": 24,
            },
        },
        "required": ["date"],
    }

    def __init__(self):
        self.service = squash_service

    async def run(self, tool_input: dict, user_context: dict) -> AsyncGenerator[ToolEvent, None]:

        try:
            date = tool_input["date"]
            after_hour = tool_input.get("after_hour", 0)
            before_hour = tool_input.get("before_hour", 24)

            availability = await self.service.get_availability(
                date=date,
                after_hour=after_hour,
                before_hour=before_hour,
            )

            yield ToolEvent(
                type="result",
                result=ToolCallResult(
                    status="success",
                    data={
                        "date": date,
                        "slots": availability,
                        "count": len(availability),
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
