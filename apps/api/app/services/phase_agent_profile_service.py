"""FM-111: Phase Agent Profile service — CRUD for phase-to-agent assignments."""

import uuid
import logging

from sqlalchemy import select, func as sa_func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.phase_agent_profile import PhaseAgentProfile, WorkflowPhase
from app.models.agent import Agent, AgentStatus
from app.schemas.phase_agent_profile import PhaseAgentProfileCreate, PhaseAgentProfileUpdate

logger = logging.getLogger(__name__)


async def list_profiles(
    db: AsyncSession,
    project_id: uuid.UUID,
) -> tuple[list[PhaseAgentProfile], int]:
    """Return all phase profiles for a project."""
    query = select(PhaseAgentProfile).where(
        PhaseAgentProfile.project_id == project_id
    )
    count_result = await db.execute(
        select(sa_func.count()).select_from(query.subquery())
    )
    total = count_result.scalar_one()

    result = await db.execute(query.order_by(PhaseAgentProfile.phase))
    return list(result.scalars().all()), total


async def get_profile_for_phase(
    db: AsyncSession,
    project_id: uuid.UUID,
    phase: WorkflowPhase,
) -> PhaseAgentProfile | None:
    """Return the active profile for a specific phase, or None."""
    result = await db.execute(
        select(PhaseAgentProfile).where(
            PhaseAgentProfile.project_id == project_id,
            PhaseAgentProfile.phase == phase,
        )
    )
    return result.scalar_one_or_none()


async def get_agent_slug_for_phase(
    db: AsyncSession,
    project_id: uuid.UUID,
    phase: WorkflowPhase,
) -> str | None:
    """Resolve the agent slug assigned to a phase for a project.

    Returns None if no profile exists.
    """
    profile = await get_profile_for_phase(db, project_id, phase)
    if profile is None:
        return None
    # Look up the agent to get its slug
    result = await db.execute(select(Agent).where(Agent.id == profile.agent_id))
    agent = result.scalar_one_or_none()
    if agent is None or agent.status != AgentStatus.ACTIVE:
        return None
    return agent.slug


async def upsert_profile(
    db: AsyncSession,
    project_id: uuid.UUID,
    data: PhaseAgentProfileCreate,
) -> PhaseAgentProfile:
    """Create or update a phase-agent assignment for a project.

    Uses the unique (project_id, phase) constraint — if an assignment
    already exists for that phase, it is updated in place.
    """
    # Validate agent exists and is active
    agent_result = await db.execute(select(Agent).where(Agent.id == data.agent_id))
    agent = agent_result.scalar_one_or_none()
    if agent is None:
        raise ValueError(f"Agent {data.agent_id} not found")
    if agent.status != AgentStatus.ACTIVE:
        raise ValueError(f"Agent {agent.slug} is not active")

    existing = await get_profile_for_phase(db, project_id, data.phase)
    if existing:
        existing.agent_id = data.agent_id
        existing.priority = data.priority
        existing.is_default = data.is_default
        existing.notes = data.notes
        db.add(existing)
        await db.flush()
        await db.refresh(existing)
        logger.info("Updated phase profile %s/%s → %s", project_id, data.phase.value, agent.slug)
        return existing

    profile = PhaseAgentProfile(
        project_id=project_id,
        phase=data.phase,
        agent_id=data.agent_id,
        priority=data.priority,
        is_default=data.is_default,
        notes=data.notes,
    )
    db.add(profile)
    await db.flush()
    await db.refresh(profile)
    logger.info("Created phase profile %s/%s → %s", project_id, data.phase.value, agent.slug)
    return profile


async def delete_profile(
    db: AsyncSession,
    project_id: uuid.UUID,
    phase: WorkflowPhase,
) -> bool:
    """Delete the phase-agent assignment for a specific phase. Returns True if deleted."""
    result = await db.execute(
        delete(PhaseAgentProfile).where(
            PhaseAgentProfile.project_id == project_id,
            PhaseAgentProfile.phase == phase,
        )
    )
    deleted = result.rowcount > 0  # type: ignore[union-attr]
    if deleted:
        logger.info("Deleted phase profile %s/%s", project_id, phase.value)
    return deleted


async def bulk_set_profiles(
    db: AsyncSession,
    project_id: uuid.UUID,
    profiles: list[PhaseAgentProfileCreate],
) -> list[PhaseAgentProfile]:
    """Set multiple phase profiles at once (used by template seeding)."""
    results = []
    for data in profiles:
        profile = await upsert_profile(db, project_id, data)
        results.append(profile)
    return results
