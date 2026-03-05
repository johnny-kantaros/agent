from abc import ABC, abstractmethod
from typing import Dict, Any


class Tool(ABC):
    name: str
    description: str
    parameters: Dict[str, Any]


    def schema(self):

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }

    @abstractmethod
    def run(self, tool_input: dict, user_context: dict) -> dict:
        pass