from fastapi import APIRouter
from pydantic import BaseModel

from ..services.agent import run_agent

router = APIRouter(prefix="/api/v1/agent", tags=["agent"])


class Message(BaseModel):
    role: str   # "user" | "assistant" | "system"
    content: str


class ChatRequest(BaseModel):
    messages: list[Message]
    user_jwt: str | None = None   # forwarded from frontend, not used yet


class ChatResponse(BaseModel):
    response: str


@router.post("/chat", response_model=ChatResponse)
async def chat(body: ChatRequest) -> ChatResponse:
    # Convert pydantic objects to plain dicts for the agent
    conversation = [{"role": m.role, "content": m.content} for m in body.messages]
    answer = await run_agent(conversation)
    return ChatResponse(response=answer)
