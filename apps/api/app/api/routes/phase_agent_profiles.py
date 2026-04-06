"""FM-111/113: Phase Agent Profile routes — CRUD for phase-to-agent assignments."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user_id
from app.db.session import get_db
from app.models.phase_agent_profile import WorkflowPhase
from app.schemas.phase_agent_profile import (
    PhaseAgentProfileCreate,
    PhaseAgentProfileList,
    PhaseAgentProfileRead,
)
from app.services import phase_agent_profile_service
from app.services.authz_service import check_project_permission, Action

router = APIRouter()


@router.get(
    "/projects/{project_id}/phase-agent-profiles",
    response_model=PhaseAgentProfileList,
)
async def list_profiles(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """List all phase-agent profiles for a project."""
    await check_project_permission(db, project_id, user_id, Action.PROJECT_VIEW)
    items, total = await phase_agent_profile_service.list_profiles(db, project_id)
    return PhaseAgentProfileList(items=items, total=total)


@router.get(
    "/projects/{project_id}/phase-agent-profiles/{phase}",
    response_model=PhaseAgentProfileRead,
)
async def get_profile(
    project_id: uuid.UUID,
    phase: WorkflowPhase,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Get the agent profile for a specific phase."""
    await check_project_permission(db, project_id, user_id, Action.PROJECT_VIEW)
    profile = await phase_agent_profile_service.get_profile_for_phase(
        db, project_id, phase
    )
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No agent profile for phase '{phase.value}'",
        )
    return profile


@router.put(
    "/projects/{project_id}/phase-agent-profiles/{phase}",
    response_model=PhaseAgentProfileRead,
)
async def upsert_profile(
    project_id: uuid.UUID,
    phase: WorkflowPhase,
    data: PhaseAgentProfileCreate,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Create or update the agent assignment for a phase."""
    await check_project_permission(db, project_id, user_id, Action.PROJECT_UPDATE)

    # Enforce path/body consistency
    if data.phase != phase:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Path phase '{phase.value}' does not match body phase '{data.phase.value}'",
        )

    try:
        return await phase_agent_profile_service.upsert_profile(db, project_id, data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete(
    "/projects/{project_id}/phase-agent-profiles/{phase}",
    status_code=204,
)
async def delete_profile(
    project_id: uuid.UUID,
    phase: WorkflowPhase,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Remove the agent assignment for a phase."""
    await check_project_permission(db, project_id, user_id, Action.PROJECT_UPDATE)
    deleted = await phase_agent_profile_service.delete_profile(db, project_id, phase)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No agent profile for phase '{phase.value}'",
        )
