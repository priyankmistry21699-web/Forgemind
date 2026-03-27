"""Governance policy routes — manage and evaluate approval policies.

FM-048: CRUD + policy evaluation endpoints.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.governance import (
    GovernancePolicyRead,
    GovernancePolicyList,
    GovernancePolicyCreate,
    GovernancePolicyUpdate,
)
from app.services import governance_service

router = APIRouter(prefix="/governance")


@router.post("/policies", response_model=GovernancePolicyRead, status_code=201)
async def create_policy(
    body: GovernancePolicyCreate,
    db: AsyncSession = Depends(get_db),
) -> GovernancePolicyRead:
    """Create a new governance policy."""
    policy = await governance_service.create_policy(
        db,
        name=body.name,
        description=body.description,
        trigger=body.trigger,
        action=body.action,
        rules=body.rules,
        project_id=body.project_id,
        enabled=body.enabled,
        priority=body.priority,
    )
    await db.commit()
    return GovernancePolicyRead.model_validate(policy)


@router.get("/policies", response_model=GovernancePolicyList)
async def list_policies(
    project_id: uuid.UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> GovernancePolicyList:
    """List governance policies, optionally filtered by project."""
    policies = await governance_service.list_policies(
        db, project_id=project_id
    )
    return GovernancePolicyList(
        items=[GovernancePolicyRead.model_validate(p) for p in policies],
        total=len(policies),
    )


@router.get("/policies/{policy_id}", response_model=GovernancePolicyRead)
async def get_policy(
    policy_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> GovernancePolicyRead:
    """Get a single policy by ID."""
    policy = await governance_service.get_policy(db, policy_id)
    if policy is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Policy not found",
        )
    return GovernancePolicyRead.model_validate(policy)


@router.patch("/policies/{policy_id}", response_model=GovernancePolicyRead)
async def update_policy(
    policy_id: uuid.UUID,
    body: GovernancePolicyUpdate,
    db: AsyncSession = Depends(get_db),
) -> GovernancePolicyRead:
    """Update a governance policy."""
    policy = await governance_service.update_policy(
        db,
        policy_id,
        **body.model_dump(exclude_unset=True),
    )
    if policy is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Policy not found",
        )
    await db.commit()
    return GovernancePolicyRead.model_validate(policy)


@router.delete("/policies/{policy_id}", status_code=204)
async def delete_policy(
    policy_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Delete a governance policy."""
    deleted = await governance_service.delete_policy(db, policy_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Policy not found",
        )
    await db.commit()


@router.get("/evaluate/task")
async def evaluate_task_approval(
    task_type: str = Query(...),
    project_id: uuid.UUID = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Evaluate whether a task type requires approval under current policies."""
    action = await governance_service.evaluate_task_approval(
        db, task_type=task_type, project_id=project_id
    )
    return {
        "task_type": task_type,
        "project_id": str(project_id),
        "action": action.value,
    }


@router.post("/seed-defaults")
async def seed_defaults(
    db: AsyncSession = Depends(get_db),
):
    """Seed default governance policies (architecture + review approval gates)."""
    policies = await governance_service.seed_default_policies(db)
    await db.commit()
    return {
        "seeded": len(policies),
        "policies": [GovernancePolicyRead.model_validate(p) for p in policies],
    }
