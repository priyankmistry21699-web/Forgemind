"""Chat routes — execution chatbot and slash command handling.

FM-044: Enhanced context assembly + topic detection + LLM.
FM-104: Slash command parsing for spec-driven workflow phases.
"""

import uuid
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user_id
from app.db.session import get_db
from app.services import chat_service
from app.services import slash_command_service

router = APIRouter()


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str
    topics: list[str]
    # FM-104: Slash command result (present only when a command was executed)
    command_result: dict[str, Any] | None = None


@router.post("/runs/{run_id}/chat", response_model=ChatResponse)
async def chat_about_run(
    run_id: uuid.UUID,
    data: ChatRequest,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> ChatResponse:
    """Ask the execution chatbot a question about a specific run.

    FM-104: If the message starts with a slash command (/fm.*), it is
    parsed and routed to the appropriate service. Normal chat continues
    for all other messages.
    """
    # FM-104: Check for slash commands first
    parsed = slash_command_service.parse_command(data.message)
    if parsed is not None:
        result = await slash_command_service.execute_command(db, run_id, parsed)
        return ChatResponse(
            reply=result.summary,
            topics=[f"command:{result.command}"],
            command_result={
                "command": result.command,
                "action": result.action,
                "success": result.success,
                "artifact_id": result.artifact_id,
                "run_id": result.run_id,
                "task_ids": result.task_ids,
                "details": result.details,
            },
        )

    # Normal chat flow
    topics = chat_service.detect_topics(data.message)
    reply = await chat_service.chat_about_run(db, run_id, data.message)
    return ChatResponse(reply=reply, topics=topics)


@router.get("/chat/commands")
async def list_commands(
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """List available slash commands for autocomplete."""
    return {"commands": slash_command_service.list_commands()}
