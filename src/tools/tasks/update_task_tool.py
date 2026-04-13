from src.tools.base import Tool
from src.tools.tasks.task_service import TaskService


class UpdateTaskTool(Tool):
    name = "update_task"
    description = """
    Update a task by its ID with partial field updates.
    Always call list_tasks before this tool to get the correct task id.
    """

    parameters = {
        "type": "object",
        "properties": {
            "task_id": {"type": "integer", "description": "ID of the task to update"},
            "updates": {
                "type": "object",
                "description": "Fields to update on the task",
                "properties": {
                    "task": {"type": "string"},
                    "details": {
                        "type": "string",
                    },
                    "due_date": {"type": "string"},
                    "reminder_cadence": {"type": "string"},
                    "completed": {"type": "integer", "description": "0 or 1"},
                },
                "additionalProperties": True,
            },
        },
        "required": ["task_id", "updates"],
    }

    def __init__(self):
        self.service = TaskService()

    async def run(self, tool_input: dict, user_context: dict) -> dict:
        try:
            self.service.update_task(task_id=tool_input["task_id"], updates=tool_input["updates"])
            return {"success": True}

        except Exception as e:
            return {"success": False, "error": str(e)}
