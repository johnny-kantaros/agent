from collections.abc import AsyncGenerator

from src.models.interface import ToolCallResult, ToolEvent
from src.tools.base import Tool
from src.tools.tasks.task_service import TaskService


class UpdateTaskTool(Tool):
    name = "update_task"
    description = """
    Update a task by its ID with partial field updates.
    Always call list_tasks before this tool to get the correct task id.
    """
    progress_indicator_message = "Updating task..."

    parameters = {
        "type": "object",
        "properties": {
            "task_id": {
                "type": "integer",
                "description": "ID of the task to update",
            },
            "updates": {
                "type": "object",
                "description": "Fields to update on the task",
                "properties": {
                    "task": {"type": "string"},
                    "details": {"type": "string"},
                    "due_date": {"type": "string"},
                    "reminder_cadence": {"type": "string"},
                    "completed": {
                        "type": "integer",
                        "description": "0 or 1",
                    },
                },
                "additionalProperties": True,
            },
        },
        "required": ["task_id", "updates"],
    }

    def __init__(self):
        self.service = TaskService()

    async def run(
        self,
        tool_input: dict,
        user_context: dict,
    ) -> AsyncGenerator[ToolEvent, None]:

        try:
            self.service.update_task(
                task_id=tool_input["task_id"],
                updates=tool_input["updates"],
            )

            yield ToolEvent(
                type="result",
                result=ToolCallResult(
                    status="success",
                    data={
                        "task_id": tool_input["task_id"],
                        "updated": True,
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
