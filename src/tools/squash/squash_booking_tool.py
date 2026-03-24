from src.tools.base import Tool
from src.tools.squash.squash_service import squash_service


class SquashBookingTool(Tool):
    name = "squash_court_booker"
    description = "Books a squash court for a given date, time, and court selection"

    parameters = {
        "type": "object",
        "properties": {
            "date": {
                "type": "string",
                "description": "Date to book in YYYY-MM-DD format",
            },
            "time_from": {
                "type": "number",
                "description": "Start time in minutes from midnight (e.g., 435 for 7:15 AM)",
            },
            "time_to": {
                "type": "number",
                "description": "End time in minutes from midnight",
            },
            "court_id": {
                "type": "string",
                "description": "ID of the court to book",
            },
            "category_options_id": {
                "type": "string",
                "description": "Category options ID for the court",
            },
            "time_slot_id": {
                "type": "string",
                "description": "Time slot ID for the booking",
            },
        },
        "required": [
            "date",
            "time_from",
            "time_to",
            "court_id",
            "category_options_id",
            "time_slot_id",
        ],
    }

    def __init__(self):
        self.service = squash_service

    async def run(self, tool_input: dict, user_context: dict) -> dict:
        """
        Calls the full book_court sequence: login, create, get temp, confirm
        """
        date = tool_input["date"]
        time_from = tool_input["time_from"]
        time_to = tool_input["time_to"]
        court_id = tool_input["court_id"]
        category_options_id = tool_input["category_options_id"]
        time_slot_id = tool_input["time_slot_id"]

        confirmed_booking = await self.service.book_court(
            date=date,
            time_from=time_from,
            time_to=time_to,
            court_id=court_id,
            category_options_id=category_options_id,
            time_slot_id=time_slot_id,
        )

        return {
            "date": date,
            "court_id": court_id,
            "time_from": time_from,
            "time_to": time_to,
            "confirmed_booking": confirmed_booking,
        }
