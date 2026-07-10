from collections.abc import AsyncGenerator

from src.models.interface import ToolCallResult, ToolEvent
from src.tools.base import Tool
from src.tools.news.news_service import news_service


class NewsAPITool(Tool):
    name = "get_news"
    description = (
        "Fetch top news headlines by category. "
        "Use for politics, world news, sports, business, or general top stories. "
        "Returns headlines with source and description."
    )

    parameters = {
        "type": "object",
        "properties": {
            "category": {
                "type": "string",
                "enum": ["general", "world", "politics", "sports", "business", "entertainment"],
                "description": "News category. Use 'general' for top stories, 'world' for international news.",
            },
            "query": {
                "type": "string",
                "description": "Optional keyword to filter headlines.",
            },
            "max_results": {
                "type": "integer",
                "description": "Number of headlines to return (default 8).",
                "default": 8,
            },
        },
        "required": ["category"],
    }

    def __init__(self):
        self.service = news_service

    async def run(self, tool_input: dict, user_context: dict) -> AsyncGenerator[ToolEvent, None]:
        try:
            articles = self.service.get_headlines(
                category=tool_input["category"],
                query=tool_input.get("query"),
                max_results=tool_input.get("max_results", 8),
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
