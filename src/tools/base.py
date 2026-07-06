from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from typing import Any

from src.models.interface import ToolEvent

_STATUS_PARAM = {
    "type": "string",
    "description": "One short sentence shown to the user before this tool runs (e.g. 'Searching for flights from SFO to JFK on July 15th...')",
}


class Tool(ABC):
    name: str
    description: str
    parameters: dict[str, Any]

    def schema(self):
        params = self.parameters
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    **params,
                    "properties": {**params.get("properties", {}), "_status": _STATUS_PARAM},
                    "required": [*params.get("required", []), "_status"],
                },
            },
        }

    @abstractmethod
    def run(self, tool_input: dict, user_context: dict) -> AsyncGenerator[ToolEvent, None]:
        """
        Streaming tool interface.

        Yields:
            ToolEvent(progress | result)
        """
        raise NotImplementedError
