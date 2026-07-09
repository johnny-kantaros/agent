from collections.abc import AsyncGenerator

from src.models.interface import ToolCallResult, ToolEvent
from src.tools.base import Tool
from src.tools.jobs.job_service import AgentJobService


class CancelJobTool(Tool):
    name = "cancel_job"
    description = "Cancel a pending agent job. Has no effect on running or completed jobs."

    parameters = {
        "type": "object",
        "properties": {
            "job_id": {
                "type": "string",
                "description": "ID of the job to cancel.",
            },
        },
        "required": ["job_id"],
    }

    def __init__(self):
        self.service = AgentJobService()

    async def run(self, tool_input: dict, user_context: dict) -> AsyncGenerator[ToolEvent, None]:
        try:
            self.service.cancel_job(job_id=tool_input["job_id"])
            yield ToolEvent(
                type="result",
                result=ToolCallResult(status="success", data={"job_id": tool_input["job_id"]}),
            )
        except Exception as e:
            yield ToolEvent(
                type="result",
                result=ToolCallResult(status="failure", data={"error": str(e)}),
            )
