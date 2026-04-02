import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user_id
from app.db.session import get_db
from app.services import chat_service

router = APIRouter()


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str
    topics: list[str]


@router.post("/runs/{run_id}/chat", response_model=ChatResponse)
async def chat_about_run(
    run_id: uuid.UUID,
    data: ChatRequest,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> ChatResponse:
    """Ask the execution chatbot a question about a specific run."""
    topics = chat_service.detect_topics(data.message)
    reply = await chat_service.chat_about_run(db, run_id, data.message)
    return ChatResponse(reply=reply, topics=topics)
