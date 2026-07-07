from collections.abc import AsyncGenerator

from src.models.interface import ToolCallResult, ToolEvent
from src.tools.base import Tool
from src.tools.gmail.gmail_service import gmail_service


class GmailSearchTool(Tool):
    name = "gmail_search"
    description = """
    Search and read emails in Gmail. Uses Gmail search syntax (same as the Gmail search bar).
    Examples: "from:john@example.com", "subject:invoice", "is:unread", "after:2026/07/01".
    Returns up to 75 email summaries including sender, subject, date, and snippet.
    Use gmail_get_message to fetch the full body of a specific email.
    """

    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Gmail search query (e.g. 'from:boss@company.com is:unread').",
            },
        },
        "required": ["query"],
    }

    def __init__(self):
        self.service = gmail_service

    async def run(self, tool_input: dict, user_context: dict) -> AsyncGenerator[ToolEvent, None]:
        try:
            results = self.service.search(query=tool_input["query"])
            yield ToolEvent(
                type="result",
                result=ToolCallResult(
                    status="success", data={"emails": results, "count": len(results)}
                ),
            )
        except Exception as e:
            yield ToolEvent(
                type="result",
                result=ToolCallResult(status="failure", data={"error": str(e)}),
            )
