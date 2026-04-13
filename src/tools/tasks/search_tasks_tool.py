from src.tools.base import Tool
from src.tools.tasks.task_service import TaskService


class SearchTasksTool(Tool):
    name = "search_tasks"
    description = "Search for a specific task."

    parameters = {
        "type": "object",
        "properties": {"task_query": {"type": "string", "description": "Query to search for task"}},
        "required": ["task_query"],
    }

    def __init__(self):
        self.service = TaskService()

    async def run(self, tool_input: dict, user_context: dict) -> dict:
        try:
            tasks = self.service.search_tasks(query=tool_input["task_query"])

            return {"success": True, "tasks": tasks}

        except Exception as e:
            return {"success": False, "error": str(e)}
