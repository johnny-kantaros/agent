from collections.abc import AsyncGenerator

from src.models.interface import ToolCallResult, ToolEvent
from src.tools.base import Tool
from src.tools.tasks.task_service import TaskService


class ListTasksTool(Tool):
    name = "list_tasks"
    description = (
        "List user tasks. "
        "Be concise when returning results — omit empty fields and task IDs, use a structured list."
    )

    parameters = {
        "type": "object",
        "properties": {
            "include_completed": {
                "type": "boolean",
                "description": "Include completed tasks. Defaults to false.",
            },
        },
        "required": [],
    }

    def __init__(self):
        self.service = TaskService()

    async def run(self, tool_input: dict, user_context: dict) -> AsyncGenerator[ToolEvent, None]:
        try:
            tasks = self.service.list_tasks(
                include_completed=tool_input.get("include_completed", False)
            )
            yield ToolEvent(
                type="result",
                result=ToolCallResult(status="success", data={"tasks": tasks, "count": len(tasks)}),
            )
        except Exception as e:
            yield ToolEvent(
                type="result",
                result=ToolCallResult(status="failure", data={"error": str(e)}),
            )
