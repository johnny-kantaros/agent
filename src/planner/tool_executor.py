import json
import logging

from src.models.interface import ToolEvent
from src.tools.registry import TOOLS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ToolExecutor:
    """Executes a single tool"""

    async def run_tool(self, tool_call, user_context=None):
        user_context = user_context or {}

        tool_name = tool_call.function.name
        tool_call_id = tool_call.id

        try:
            args = json.loads(tool_call.function.arguments)
        except json.JSONDecodeError:
            args = {}

        tool = TOOLS.get(tool_name)
        tool_result = None

        if tool:
            try:
                async for event in tool.run(args, user_context=user_context):
                    yield event
            except Exception as e:
                tool_result = {"error": str(e)}

        else:
            tool_result = {"error": f"Tool '{tool_name}' not found"}

        if tool_result is None:
            tool_result = {"error": "Tool did not return result"}

        yield ToolEvent(
            type="result",
            result={
                "tool_call_id": tool_call_id,
                "content": json.dumps(tool_result),
            },
        )
