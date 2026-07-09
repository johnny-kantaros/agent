from collections.abc import AsyncGenerator

from src.models.interface import ToolCallResult, ToolEvent
from src.tools.base import Tool
from src.tools.jobs.job_service import AgentJobService


class ScheduleJobTool(Tool):
    name = "schedule_job"
    description = (
        "Schedule a job for the agent to execute autonomously at a future time. "
        "Use ONLY when the agent needs to actively do something: book a court, search emails, summarize a calendar, check prices, etc. "
        "Do NOT use this for simple reminders — use create_task with scheduled_at for those. "
        "Recurrence uses cron syntax: '0 8 * * 1' = every Monday at 8am. "
        "Results are sent to the user via the specified channels."
    )

    parameters = {
        "type": "object",
        "properties": {
            "instruction": {
                "type": "string",
                "description": "What the agent should do when the job runs.",
            },
            "scheduled_at": {
                "type": "string",
                "description": "When to run the job (ISO 8601). For recurring jobs, this is the first run time.",
            },
            "recurrence": {
                "type": "string",
                "description": "Cron expression for recurring jobs (e.g. '0 8 * * 1'). Omit for one-off jobs.",
            },
            "notify_via": {
                "type": "array",
                "items": {"type": "string", "enum": ["telegram", "email"]},
                "description": "Channels to notify when the job completes. Defaults to ['telegram'].",
            },
        },
        "required": ["instruction", "scheduled_at"],
    }

    def __init__(self):
        self.service = AgentJobService()

    async def run(self, tool_input: dict, user_context: dict) -> AsyncGenerator[ToolEvent, None]:
        try:
            result = self.service.create_job(
                instruction=tool_input["instruction"],
                scheduled_at=tool_input["scheduled_at"],
                recurrence=tool_input.get("recurrence"),
                notify_via=tool_input.get("notify_via", ["telegram"]),
            )
            yield ToolEvent(
                type="result",
                result=ToolCallResult(status="success", data=result),
            )
        except Exception as e:
            yield ToolEvent(
                type="result",
                result=ToolCallResult(status="failure", data={"error": str(e)}),
            )
