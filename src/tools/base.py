from abc import ABC, abstractmethod

class Tool(ABC):
    name: str
    description: str

    @abstractmethod
    def run(self, tool_input: dict, user_context: dict) -> dict:
        pass