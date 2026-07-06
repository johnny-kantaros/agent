from collections.abc import AsyncGenerator

from src.models.interface import ToolCallResult, ToolEvent
from src.tools.base import Tool
from src.tools.tasks.task_service import TaskService


class CompleteTaskTool(Tool):
    name = "complete_task"
    description = """
    Mark a task as complete or closed.
    Always call list_tasks before this tool to get the correct task id.
    """
    parameters = {
        "type": "object",
        "properties": {
            "task_id": {
                "type": "integer",
                "description": "ID of the task to update",
            }
        },
        "required": ["task_id"],
    }

    def __init__(self):
        self.service = TaskService()

    async def run(
        self,
        tool_input: dict,
        user_context: dict,
    ) -> AsyncGenerator[ToolEvent, None]:

        try:
            task_id = tool_input["task_id"]
            self.service.complete_task(task_id)

            yield ToolEvent(
                type="result",
                result=ToolCallResult(
                    status="success",
                    data={
                        "task_id": task_id,
                        "completed": True,
                    },
                ),
            )

        except Exception as e:
            yield ToolEvent(
                type="result",
                result=ToolCallResult(
                    status="failure",
                    data={
                        "task_id": tool_input.get("task_id"),
                        "error": str(e),
                    },
                ),
            )
