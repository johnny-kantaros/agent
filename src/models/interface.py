from dataclasses import dataclass
from typing import Any, Literal


@dataclass
class RequestContext:
    chat_id: int
    user_id: int
    text: str


@dataclass
class ToolCallResult:
    status: Literal["success", "failure"]
    data: dict[str, Any]


@dataclass
class ToolEvent:
    type: Literal["progress", "result"]
    message: str | None = None
    result: ToolCallResult | None = None
    tool: str | None = None


@dataclass
class AgentUpdate:
    type: Literal["progress", "final"]
    message: str
