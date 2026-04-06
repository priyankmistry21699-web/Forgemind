"""FM-102/103: Constitution service — CRUD and prompt injection for project constitutions.

Includes governance audit hooks: constitution changes emit events visible
in the project audit trail.
"""

import uuid
import logging

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project_constitution import ProjectConstitution
from app.models.execution_event import EventType
from app.schemas.constitution import ConstitutionCreate, ConstitutionUpdate
from app.services import event_service

logger = logging.getLogger(__name__)


async def get_constitution(
    db: AsyncSession,
    project_id: uuid.UUID,
) -> ProjectConstitution | None:
    """Fetch the constitution for a project, or None if not set."""
    result = await db.execute(
        select(ProjectConstitution).where(ProjectConstitution.project_id == project_id)
    )
    return result.scalar_one_or_none()


async def create_or_update_constitution(
    db: AsyncSession,
    project_id: uuid.UUID,
    data: ConstitutionCreate | ConstitutionUpdate,
) -> ProjectConstitution:
    """Create or update the project constitution (upsert)."""
    existing = await get_constitution(db, project_id)

    if existing is None:
        if isinstance(data, ConstitutionUpdate):
            content = data.content
            if content is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Content is required when creating a constitution",
                )
        else:
            content = data.content

        constitution = ProjectConstitution(
            project_id=project_id,
            content=content,
            title=data.title,
            summary=data.summary,
            version=1,
        )
        db.add(constitution)
    else:
        update_data = data.model_dump(exclude_unset=True)
        if update_data:
            if "content" in update_data:
                existing.version += 1
            for field, value in update_data.items():
                setattr(existing, field, value)
        constitution = existing

    await db.flush()
    await db.refresh(constitution)

    # FM-103: Governance audit event
    action = "created" if existing is None else "updated"
    await event_service.emit_event(
        db,
        event_type=EventType.CONSTITUTION_UPDATED,
        summary=f"Project constitution {action} (v{constitution.version})",
        project_id=project_id,
        metadata={
            "action": action,
            "version": constitution.version,
            "title": constitution.title,
        },
    )

    return constitution


async def delete_constitution(
    db: AsyncSession,
    project_id: uuid.UUID,
) -> bool:
    """Delete the constitution for a project. Returns True if deleted."""
    constitution = await get_constitution(db, project_id)
    if constitution is None:
        return False
    await db.delete(constitution)
    await db.flush()

    # FM-103: Governance audit event
    await event_service.emit_event(
        db,
        event_type=EventType.CONSTITUTION_UPDATED,
        summary="Project constitution deleted",
        project_id=project_id,
        metadata={"action": "deleted"},
    )

    return True


def build_constitution_prompt_section(content: str) -> str:
    """Format constitution content as a prompt injection section."""
    return (
        "=== Project Constitution ===\n"
        "The following rules and constraints MUST be followed for all actions "
        "in this project. Violations are not acceptable.\n\n"
        f"{content}\n"
        "=== End Constitution ===\n"
    )


async def get_constitution_for_prompt(
    db: AsyncSession,
    project_id: uuid.UUID,
) -> str | None:
    """Get the constitution formatted for prompt injection, or None."""
    constitution = await get_constitution(db, project_id)
    if constitution is None:
        return None
    return build_constitution_prompt_section(constitution.content)
