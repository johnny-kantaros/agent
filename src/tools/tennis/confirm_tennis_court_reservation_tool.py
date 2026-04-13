from src.tools.base import Tool
from src.tools.tennis.tennis_service import tennis_service
from src.utils.constants import COURTS


class TennisCourtConfirmTool(Tool):
    name = "confirm_tennis_court_reservation"

    description = """
    Confirms a pending tennis court reservation using the SMS verification code sent to the user.

    This finalizes the reservation created by start_tennis_court_reservation.

    Use this tool after the user provides the verification code they received via SMS.
    """

    ALLOWED_COURTS = list(COURTS.keys())

    parameters = {
        "type": "object",
        "properties": {
            "verification_code": {
                "type": "string",
                "description": "The SMS/TOTP verification code sent to the user's phone.",
            }
        },
        "required": ["reservation_id", "verification_code"],
    }

    def __init__(self):
        self.service = tennis_service

    async def run(self, tool_input: dict, user_context: dict) -> dict:
        confirm_response: dict = self.service.confirm_reservation(
            confirmation_code=tool_input["verification_code"]
        )
        return {"response": confirm_response}
