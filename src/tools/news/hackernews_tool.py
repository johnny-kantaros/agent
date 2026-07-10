from collections.abc import AsyncGenerator

from src.models.interface import ToolCallResult, ToolEvent
from src.tools.base import Tool
from src.tools.news.news_service import news_service


class HackerNewsTool(Tool):
    name = "get_tech_news"
    description = (
        "Fetch top stories from Hacker News. "
        "Use for tech, startup, and programming news. No API key required."
    )

    parameters = {
        "type": "object",
        "properties": {
            "limit": {
                "type": "integer",
                "description": "Number of stories to return (default 10).",
                "default": 10,
            },
            "min_score": {
                "type": "integer",
                "description": "Only return stories with at least this many points (default 50).",
                "default": 50,
            },
        },
        "required": [],
    }

    def __init__(self):
        self.service = news_service

    async def run(self, tool_input: dict, user_context: dict) -> AsyncGenerator[ToolEvent, None]:
        try:
            stories = self.service.get_top_hn_stories(
                limit=tool_input.get("limit", 10),
                min_score=tool_input.get("min_score", 50),
            )
            yield ToolEvent(
                type="result",
                result=ToolCallResult(
                    status="success", data={"stories": stories, "count": len(stories)}
                ),
            )
        except Exception as e:
            yield ToolEvent(
                type="result",
                result=ToolCallResult(status="failure", data={"error": str(e)}),
            )
