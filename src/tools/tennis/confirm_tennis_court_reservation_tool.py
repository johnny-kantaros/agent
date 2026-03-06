from src.tools.base import Tool
from src.tools.tennis.tennis_service import TennisService
from src.utils.constants import COURTS


class TennisCourtConfirmTool(Tool):
    name = "confirm_tennis_court_reservation"

    description = (
    """
    Confirms a pending tennis court reservation using the SMS verification code sent to the user.

    This finalizes the reservation created by start_tennis_court_reservation.

    Use this tool after the user provides the verification code they received via SMS.
    """
    )

    ALLOWED_COURTS = list(COURTS.keys())

    parameters = {
        "type": "object",
        "properties": {
            "reservation_id": {
                "type": "string",
                "description": "The pending reservation ID returned from start_tennis_court_reservation."
            },
            "verification_code": {
                "type": "string",
                "description": "The SMS/TOTP verification code sent to the user's phone."
            }
        },
        "required": ["reservation_id", "verification_code"]
    }

    def __init__(self):
        self.service = TennisService()

    def run(self, tool_input: dict, user_context: dict) -> dict:
        init_res = self.service.init_reservation(court_name=tool_input["court_name"], court_number=tool_input["court_number"], date=tool_input["date"], start_time=tool_input["start_time"], end_time=tool_input["end_time"])
