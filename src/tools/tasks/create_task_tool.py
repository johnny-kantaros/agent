from collections.abc import AsyncGenerator

from src.models.interface import ToolCallResult, ToolEvent
from src.tools.base import Tool
from src.tools.tasks.task_service import TaskService


class CreateTaskTool(Tool):
    name = "create_task"
    description = (
        "Create a new user task. "
        "Set scheduled_at to remind the user at a specific time. "
        "Set recurrence (cron expression) for repeating reminders. "
        "Just create the task — do not ask for extra details unless provided."
    )

    parameters = {
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "Short, descriptive task name (a few words).",
            },
            "description": {
                "type": "string",
                "description": "Optional additional details.",
            },
            "priority": {
                "type": "string",
                "enum": ["low", "medium", "high"],
                "description": "Optional priority level.",
            },
            "due_date": {
                "type": "string",
                "description": "Optional deadline (ISO 8601).",
            },
            "scheduled_at": {
                "type": "string",
                "description": "When to send a reminder (ISO 8601). Omit if no reminder needed.",
            },
            "recurrence": {
                "type": "string",
                "description": "Cron expression for repeating reminders (e.g. '0 9 * * *' = daily at 9am). Requires scheduled_at.",
            },
            "notify_via": {
                "type": "array",
                "items": {"type": "string", "enum": ["telegram", "email"]},
                "description": "Reminder channels. Defaults to ['telegram'].",
            },
        },
        "required": ["title"],
    }

    def __init__(self):
        self.service = TaskService()

    async def run(self, tool_input: dict, user_context: dict) -> AsyncGenerator[ToolEvent, None]:
        try:
            result = self.service.create_task(tool_input)
            yield ToolEvent(
                type="result",
                result=ToolCallResult(status="success", data=result),
            )
        except Exception as e:
            yield ToolEvent(
                type="result",
                result=ToolCallResult(status="failure", data={"error": str(e)}),
            )
