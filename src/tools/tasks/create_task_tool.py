from collections.abc import AsyncGenerator

from src.models.interface import ToolCallResult, ToolEvent
from src.tools.base import Tool
from src.tools.tasks.task_service import TaskService


class CreateTaskTool(Tool):
    name = "create_task"
    description = """
    Create a new task with optional due date, details and reminder cadence.
    Adhere to the following instructions:
        1. The task name should be short and descriptive (only a few words). 
        2. Only include details if provided by the user. If provided, they should also be stored very concisely.
        3. Just make the task provided - do NOT ask for details, reminders, etc.
    """
    progress_indicator_message = "Creating task..."

    parameters = {
        "type": "object",
        "properties": {
            "task": {"type": "string", "description": "The task description"},
            "due_date": {
                "type": "string",
                "description": "Optional due date (ISO format preferred)",
            },
            "details": {
                "type": "string",
                "description": "Optional task details",
            },
            "reminder_cadence": {
                "type": "string",
                "description": "Reminder frequency (e.g. 'daily', 'weekly', 'none')",
            },
        },
        "required": ["task"],
    }

    def __init__(self):
        self.service = TaskService()

    async def run(
        self,
        tool_input: dict,
        user_context: dict,
    ) -> AsyncGenerator[ToolEvent, None]:

        try:
            self.service.create_task(tool_input)

            yield ToolEvent(
                type="result",
                result=ToolCallResult(
                    status="success",
                    data={
                        "task": tool_input.get("task"),
                        "message": f"Task '{tool_input.get('task')}' created.",
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
                        "task": tool_input.get("task"),
                    },
                ),
            )
