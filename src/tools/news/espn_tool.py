from collections.abc import AsyncGenerator

from src.models.interface import ToolCallResult, ToolEvent
from src.tools.base import Tool
from src.tools.news.news_service import news_service

_DEFAULT_LEAGUES = ["nfl", "mlb", "nba", "tennis", "golf"]


class ESPNTool(Tool):
    name = "get_sports_news"
    description = (
        "Fetch the latest sports headlines from ESPN. "
        "Supports NFL, MLB, NBA, tennis, and golf. "
        "Returns headlines grouped by league with links."
    )

    parameters = {
        "type": "object",
        "properties": {
            "leagues": {
                "type": "array",
                "items": {"type": "string", "enum": ["nfl", "nba", "mlb", "tennis", "golf"]},
                "description": "Leagues to fetch. Defaults to all: nfl, mlb, nba, tennis, golf.",
            },
            "max_per_league": {
                "type": "integer",
                "description": "Headlines per league (default 5).",
                "default": 5,
            },
        },
        "required": [],
    }

    def __init__(self):
        self.service = news_service

    async def run(self, tool_input: dict, user_context: dict) -> AsyncGenerator[ToolEvent, None]:
        try:
            leagues = tool_input.get("leagues", _DEFAULT_LEAGUES)
            articles = self.service.get_espn_news(
                leagues=leagues,
                max_per_league=tool_input.get("max_per_league", 5),
            )
            yield ToolEvent(
                type="result",
                result=ToolCallResult(
                    status="success", data={"articles": articles, "count": len(articles)}
                ),
            )
        except Exception as e:
            yield ToolEvent(
                type="result",
                result=ToolCallResult(status="failure", data={"error": str(e)}),
            )
