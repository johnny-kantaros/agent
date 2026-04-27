from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from typing import Any

from src.models.interface import ToolEvent


class Tool(ABC):
    name: str
    description: str
    progress_indicator_message: str
    parameters: dict[str, Any]

    def schema(self):
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
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
