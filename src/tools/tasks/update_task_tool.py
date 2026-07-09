from collections.abc import AsyncGenerator

from src.models.interface import ToolCallResult, ToolEvent
from src.tools.base import Tool
from src.tools.tasks.task_service import TaskService


class UpdateTaskTool(Tool):
    name = "update_task"
    description = "Update a task by its ID. Call list_tasks first to get the correct task ID."

    parameters = {
        "type": "object",
        "properties": {
            "task_id": {
                "type": "integer",
                "description": "ID of the task to update.",
            },
            "updates": {
                "type": "object",
                "description": "Fields to update.",
                "properties": {
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "status": {
                        "type": "string",
                        "enum": ["pending", "in_progress", "completed"],
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["low", "medium", "high"],
                    },
                    "due_date": {"type": "string"},
                    "scheduled_at": {"type": "string"},
                    "recurrence": {"type": "string"},
                    "notify_via": {
                        "type": "array",
                        "items": {"type": "string", "enum": ["telegram", "email"]},
                    },
                },
            },
        },
        "required": ["task_id", "updates"],
    }

    def __init__(self):
        self.service = TaskService()

    async def run(self, tool_input: dict, user_context: dict) -> AsyncGenerator[ToolEvent, None]:
        try:
            self.service.update_task(tool_input["task_id"], tool_input["updates"])
            yield ToolEvent(
                type="result",
                result=ToolCallResult(status="success", data={"task_id": tool_input["task_id"]}),
            )
        except Exception as e:
            yield ToolEvent(
                type="result",
                result=ToolCallResult(status="failure", data={"error": str(e)}),
            )
