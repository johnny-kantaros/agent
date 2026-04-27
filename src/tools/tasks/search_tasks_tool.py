from collections.abc import AsyncGenerator

from src.models.interface import ToolCallResult, ToolEvent
from src.tools.base import Tool
from src.tools.tasks.task_service import TaskService


class SearchTasksTool(Tool):
    """This tool is not yet used"""

    name = "search_tasks"
    description = "Search for a specific task."
    progress_indicator_message = "Searching tasks..."

    parameters = {
        "type": "object",
        "properties": {"task_query": {"type": "string", "description": "Query to search for task"}},
        "required": ["task_query"],
    }

    def __init__(self):
        self.service = TaskService()

    async def run(
        self,
        tool_input: dict,
        user_context: dict,
    ) -> AsyncGenerator[ToolEvent, None]:

        try:
            tasks = self.service.search_tasks(query=tool_input["task_query"])

            yield ToolEvent(
                type="result",
                result=ToolCallResult(
                    status="success",
                    data={
                        "tasks": tasks,
                    },
                ),
            )

        except Exception as e:
            yield ToolEvent(
                type="result",
                result=ToolCallResult(
                    status="failure",
                    data={
                        "error": str(e),
                        "query": tool_input.get("task_query"),
                    },
                ),
            )
