"""FM-132: Deployment environment service — CRUD and release target management."""

from __future__ import annotations

import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.release_ops import DeploymentEnvironment
from app.schemas.release_ops import EnvironmentCreate, EnvironmentUpdate

logger = logging.getLogger(__name__)


async def create_environment(
    db: AsyncSession,
    *,
    project_id: uuid.UUID,
    data: EnvironmentCreate,
) -> DeploymentEnvironment:
    """Create a deployment environment for a project."""
    env = DeploymentEnvironment(
        project_id=project_id,
        name=data.name,
        tier=data.tier,
        description=data.description,
        config=data.config,
        required_gates=data.required_gates,
        promotion_target_id=data.promotion_target_id,
    )
    db.add(env)
    await db.flush()
    logger.info("Created environment '%s' (%s) for project %s", env.name, env.tier.value, project_id)
    return env


async def get_environment(
    db: AsyncSession,
    environment_id: uuid.UUID,
) -> DeploymentEnvironment | None:
    result = await db.execute(
        select(DeploymentEnvironment).where(DeploymentEnvironment.id == environment_id)
    )
    return result.scalar_one_or_none()


async def list_environments(
    db: AsyncSession,
    project_id: uuid.UUID,
) -> list[DeploymentEnvironment]:
    result = await db.execute(
        select(DeploymentEnvironment)
        .where(DeploymentEnvironment.project_id == project_id)
        .order_by(DeploymentEnvironment.created_at)
    )
    return list(result.scalars().all())


async def update_environment(
    db: AsyncSession,
    environment_id: uuid.UUID,
    data: EnvironmentUpdate,
) -> DeploymentEnvironment | None:
    env = await get_environment(db, environment_id)
    if env is None:
        return None

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(env, field, value)

    await db.flush()
    await db.refresh(env)
    return env


async def delete_environment(
    db: AsyncSession,
    environment_id: uuid.UUID,
) -> bool:
    env = await get_environment(db, environment_id)
    if env is None:
        return False
    await db.delete(env)
    await db.flush()
    return True
