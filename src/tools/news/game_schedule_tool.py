from collections.abc import AsyncGenerator
from datetime import datetime

from src.models.interface import ToolCallResult, ToolEvent
from src.tools.base import Tool
from src.tools.news.news_service import news_service
from src.utils.timezone import get_local_tz

_DEFAULT_LEAGUES = ["nfl", "mlb", "nba", "nhl"]


class GameScheduleTool(Tool):
    name = "get_game_schedule"
    description = (
        "Get the game schedule for a date: matchups, start times, and broadcasts. "
        "Supports NFL, MLB, NBA, and NHL. Defaults to today (user's local time) and all four leagues. "
        "Each broadcast has a market ('national', 'home', or 'away' — home/away refer to which team's "
        "side of the matchup that feed belongs to, not the viewer's location). For MLB, 'MLB.TV' is "
        "tagged national but is usually blacked out for the home team's own market — prefer the "
        "home/away regional network (e.g. NESN) over MLB.TV when picking the channel for a specific team."
    )

    parameters = {
        "type": "object",
        "properties": {
            "leagues": {
                "type": "array",
                "items": {"type": "string", "enum": ["nfl", "nba", "mlb", "nhl"]},
                "description": "Leagues to check. Defaults to all: nfl, mlb, nba, nhl.",
            },
            "date": {
                "type": "string",
                "description": "Date to check, YYYY-MM-DD. Defaults to today in the user's local timezone.",
            },
        },
        "required": [],
    }

    def __init__(self):
        self.service = news_service

    async def run(self, tool_input: dict, user_context: dict) -> AsyncGenerator[ToolEvent, None]:
        try:
            leagues = tool_input.get("leagues", _DEFAULT_LEAGUES)
            date = tool_input.get("date") or datetime.now(get_local_tz()).strftime("%Y-%m-%d")
            games = self.service.get_game_schedule(leagues=leagues, date=date.replace("-", ""))
            yield ToolEvent(
                type="result",
                result=ToolCallResult(status="success", data={"games": games, "count": len(games)}),
            )
        except Exception as e:
            yield ToolEvent(
                type="result",
                result=ToolCallResult(status="failure", data={"error": str(e)}),
            )
