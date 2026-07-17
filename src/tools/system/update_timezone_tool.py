from collections.abc import AsyncGenerator

from src.models.interface import ToolCallResult, ToolEvent
from src.tools.base import Tool
from src.tools.jobs.job_service import AgentJobService
from src.tools.tasks.task_service import TaskService
from src.utils.timezone import set_timezone_name


class UpdateTimezoneTool(Tool):
    name = "update_timezone"
    description = (
        "Update the user's current local timezone, e.g. after traveling. "
        "Affects how new task/job due dates and reminder times are interpreted and displayed, "
        "and the current-time reasoning used elsewhere. One-off deadlines/reminders already scheduled "
        "keep their exact original moment (correctly redisplayed in the new zone). Pending recurring "
        "reminders/jobs are immediately resynced to fire at the same wall-clock time in the new zone."
    )

    parameters = {
        "type": "object",
        "properties": {
            "timezone": {
                "type": "string",
                "description": "IANA timezone name, e.g. 'America/New_York', 'Europe/London'.",
            },
        },
        "required": ["timezone"],
    }

    async def run(self, tool_input: dict, user_context: dict) -> AsyncGenerator[ToolEvent, None]:
        try:
            set_timezone_name(tool_input["timezone"])
            TaskService.resync_recurring_reminders()
            AgentJobService.resync_recurring_jobs()
            yield ToolEvent(
                type="result",
                result=ToolCallResult(status="success", data={"timezone": tool_input["timezone"]}),
            )
        except ValueError as e:
            yield ToolEvent(
                type="result",
                result=ToolCallResult(status="failure", data={"error": str(e)}),
            )
