from collections.abc import AsyncGenerator

from src.models.interface import ToolCallResult, ToolEvent
from src.tools.base import Tool
from src.tools.tennis.tennis_service import tennis_service
from src.utils.constants import COURTS


class TennisCourtConfirmTool(Tool):
    name = "confirm_tennis_court_reservation"
    description = """
    Confirms a pending tennis court reservation using the SMS verification code.

    This finalizes the reservation created by start_tennis_court_reservation.
    """
    progress_indicator_message = "Confirming tennis court reservation..."

    ALLOWED_COURTS = list(COURTS.keys())

    parameters = {
        "type": "object",
        "properties": {
            "verification_code": {
                "type": "string",
                "description": "The SMS/TOTP verification code sent to the user's phone.",
            }
        },
        "required": ["verification_code"],
    }

    def __init__(self):
        self.service = tennis_service

    async def run(self, tool_input: dict, user_context: dict) -> AsyncGenerator[ToolEvent, None]:
        try:
            confirmation = self.service.confirm_reservation(
                confirmation_code=tool_input["verification_code"],
            )
            yield ToolEvent(
                type="result",
                result=ToolCallResult(
                    status="success",
                    data={
                        "response": confirmation,
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
