import json
import logging

from src.models.interface import ToolCallResult, ToolEvent
from src.tools.registry import TOOLS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ToolExecutor:
    """Executes a single tool"""

    async def run_tool(self, tool_call, user_context=None):
        user_context = user_context or {}
        tool_name = tool_call.function.name

        try:
            args = json.loads(tool_call.function.arguments)
        except json.JSONDecodeError:
            args = {}

        tool = TOOLS.get(tool_name)

        if tool:
            async for event in tool.run(args, user_context=user_context):
                yield event
        else:
            yield ToolEvent(
                type="result",
                result=ToolCallResult(
                    status="failure",
                    data={
                        "message": "Tool does not exist",
                    },
                ),
            )
