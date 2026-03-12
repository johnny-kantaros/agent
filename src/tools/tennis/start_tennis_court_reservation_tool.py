from src.tools.base import Tool
from src.tools.tennis.tennis_service import tennis_service
from src.utils.constants import COURTS


class TennisCourtBookerInitialization(Tool):
    name = "start_tennis_court_reservation"

    description = """
    Creates a pending tennis court reservation for a specific court, date, and time.

    This initializes the booking and places the reservation in a temporary cart. 
    A verification code will be sent to the user's phone via SMS.

    The reservation is not confirmed until the verification code is submitted using the confirm_tennis_court_reservation tool.

    Use this tool when the user clearly wants to book a specific tennis court and time.
    """

    ALLOWED_COURTS = list(COURTS.keys())

    parameters = {
        "type": "object",
        "properties": {
            "court_name": {
                "type": "string",
                "enum": ALLOWED_COURTS,
                "description": "Name of the court location.",
            },
            "court_number": {
                "type": "integer",
                "description": "Court number at the facility (e.g. 1,2,3,4).",
            },
            "date": {"type": "string", "description": "Reservation date in YYYY-MM-DD format"},
            "start_time": {
                "type": "string",
                "description": "Start time in HH:MM:SS military format.",
            },
            "end_time": {"type": "string", "description": "End time in HH:MM:SS military format."},
            "reservation_id": {
                "type": "string",
                "description": (
                    "Optional reservation referenceId if already known from the schedule API."
                ),
            },
        },
        "required": ["court_name", "court_number", "date", "start_time", "end_time"],
    }

    def __init__(self):
        self.service = tennis_service

    def run(self, tool_input: dict, user_context: dict) -> dict:
        reservation_id: str = self.service.init_reservation(
            court_name=tool_input["court_name"],
            court_number=tool_input["court_number"],
            date=tool_input["date"],
            start_time=tool_input["start_time"],
            end_time=tool_input["end_time"],
        )
        return {
            "response": f"The reservation process has been initiated (reservation id: {reservation_id}). A confirmation code was sent to the user. Provide that code to continue and complete the reservation."
        }
