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
        "properties": {"task_id": {"type": "integer", "description": "ID of the task to update"}},
        "required": ["task_id"],
    }

    def __init__(self):
        self.service = TaskService()

    async def run(self, tool_input: dict, user_context: dict) -> dict:
        try:
            self.service.complete_task(tool_input["task_id"])
            return {"success": True}

        except Exception as e:
            return {"success": False, "error": str(e)}
