import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services import chat_service

router = APIRouter()


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str


@router.post("/runs/{run_id}/chat", response_model=ChatResponse)
async def chat_about_run(
    run_id: uuid.UUID,
    data: ChatRequest,
    db: AsyncSession = Depends(get_db),
) -> ChatResponse:
    """Ask the execution chatbot a question about a specific run."""
    reply = await chat_service.chat_about_run(db, run_id, data.message)
    return ChatResponse(reply=reply)
