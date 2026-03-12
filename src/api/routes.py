from fastapi import APIRouter
from pydantic import BaseModel

from src.planner.agent import Agent

agent = Agent()
router = APIRouter()


class SendMessageRequest(BaseModel):
    message: str


@router.post("/message")
def send_message(data: SendMessageRequest):
    response = agent.execute(data.message)
    return {"response": response}
