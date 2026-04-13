from src.tools.base import Tool
from src.tools.tasks.task_service import TaskService


class ListTasksTool(Tool):
    name = "list_tasks"
    description = "List tasks for user."

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

    async def run(self, tool_input: dict, user_context: dict) -> dict:
        try:
            tasks = self.service.list_tasks(include_completed=tool_input["only_open_status"])

            return {"success": True, "tasks": tasks}

        except Exception as e:
            return {"success": False, "error": str(e)}
