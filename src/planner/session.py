import asyncio
import uuid

from src.planner.context import build_system_prompt


class ChatSession:
    def __init__(self) -> None:
        self.messages: list = [build_system_prompt()]
        self.lock = asyncio.Lock()

    def reset(self) -> None:
        self.messages = [build_system_prompt()]


class SessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, ChatSession] = {}

    def create(self) -> tuple[str, ChatSession]:
        session_id = str(uuid.uuid4())
        session = ChatSession()
        self._sessions[session_id] = session
        return session_id, session

    def get_or_create(self, key: str) -> ChatSession:
        if key not in self._sessions:
            self._sessions[key] = ChatSession()
        return self._sessions[key]

    def get(self, session_id: str) -> ChatSession | None:
        return self._sessions.get(session_id)

    def delete(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)
