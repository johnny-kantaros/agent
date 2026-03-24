from src.tools.base import Tool
from src.tools.squash.squash_service import squash_service


class SquashBookingTool(Tool):
    name = "squash_court_booker"
    description = """
    Call this tool when the user wants to book a squash court.
    Squash courts are always booked for 45 minutes.
    """

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
            "court_number": {
                "type": "string",
                "description": "Number of the court to book (1, 2, 3, 4, 5)",
            },
        },
        "required": [
            "date",
            "time_from",
            "time_to",
            "court_number",
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
        court_number = tool_input["court_number"]
        category_options_id = tool_input.get("category_options_id")
        time_slot_id = tool_input.get("time_slot_id")

        confirmed_booking = await self.service.book_court(
            date=date,
            time_from=time_from,
            time_to=time_to,
            court_number=court_number,
            category_options_id=category_options_id,
            time_slot_id=time_slot_id,
        )

        return {
            "date": date,
            "court_number": court_number,
            "time_from": time_from,
            "time_to": time_to,
            "confirmed_booking": confirmed_booking,
        }
