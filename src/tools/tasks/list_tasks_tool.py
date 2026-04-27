from collections.abc import AsyncGenerator

from src.models.interface import ToolCallResult, ToolEvent
from src.tools.base import Tool
from src.tools.tasks.task_service import TaskService


class ListTasksTool(Tool):
    name = "list_tasks"
    description = """
    List all tasks.
    When returning tasks to the user, adhere to the following instructions:
        1. Be as concise as possible.
        2. Do not show task id or any empty fields.
        3. Return as a structured list when possible.
    """

    parameters = {
        "type": "object",
        "properties": {
            "only_open_status": {
                "type": "boolean",
                "description": "Whether we should only list the open tasks (default is true)",
            }
        },
        "required": ["only_open_status"],
    }

    def __init__(self):
        self.service = TaskService()

    async def run(
        self,
        tool_input: dict,
        user_context: dict,
    ) -> AsyncGenerator[ToolEvent, None]:

        try:
            tasks = self.service.list_tasks(include_completed=tool_input["only_open_status"])

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
                    },
                ),
            )
