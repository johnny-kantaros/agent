from collections.abc import AsyncGenerator

from src.models.interface import ToolCallResult, ToolEvent
from src.tools.base import Tool
from src.tools.jobs.job_service import AgentJobService


class UpdateJobTool(Tool):
    name = "update_job"
    description = "Update a pending agent job's instruction, schedule, or notification channels."

    parameters = {
        "type": "object",
        "properties": {
            "job_id": {
                "type": "string",
                "description": "ID of the job to update.",
            },
            "instruction": {
                "type": "string",
                "description": "New instruction for the job.",
            },
            "scheduled_at": {
                "type": "string",
                "description": "New scheduled time (ISO 8601).",
            },
            "recurrence": {
                "type": "string",
                "description": "New cron expression, or null to make the job one-off.",
            },
            "notify_via": {
                "type": "array",
                "items": {"type": "string", "enum": ["telegram", "email"]},
                "description": "New notification channels.",
            },
        },
        "required": ["job_id"],
    }

    def __init__(self):
        self.service = AgentJobService()

    async def run(self, tool_input: dict, user_context: dict) -> AsyncGenerator[ToolEvent, None]:
        try:
            job_id = tool_input.pop("job_id")
            self.service.update_job(job_id=job_id, updates=tool_input)
            yield ToolEvent(
                type="result",
                result=ToolCallResult(status="success", data={"job_id": job_id}),
            )
        except Exception as e:
            yield ToolEvent(
                type="result",
                result=ToolCallResult(status="failure", data={"error": str(e)}),
            )
