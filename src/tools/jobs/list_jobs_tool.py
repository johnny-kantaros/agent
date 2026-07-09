from collections.abc import AsyncGenerator

from src.models.interface import ToolCallResult, ToolEvent
from src.tools.base import Tool
from src.tools.jobs.job_service import AgentJobService


class ListJobsTool(Tool):
    name = "list_jobs"
    description = "List scheduled agent jobs, optionally filtered by status."

    parameters = {
        "type": "object",
        "properties": {
            "status": {
                "type": "string",
                "enum": ["pending", "running", "done", "failed", "cancelled"],
                "description": "Filter by status. Omit to return all jobs.",
            },
        },
        "required": [],
    }

    def __init__(self):
        self.service = AgentJobService()

    async def run(self, tool_input: dict, user_context: dict) -> AsyncGenerator[ToolEvent, None]:
        try:
            jobs = self.service.list_jobs(status=tool_input.get("status"))
            yield ToolEvent(
                type="result",
                result=ToolCallResult(status="success", data={"jobs": jobs, "count": len(jobs)}),
            )
        except Exception as e:
            yield ToolEvent(
                type="result",
                result=ToolCallResult(status="failure", data={"error": str(e)}),
            )
