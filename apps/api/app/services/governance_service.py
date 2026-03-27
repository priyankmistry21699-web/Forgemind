"""Governance policy service — configurable approval rules engine.

FM-048: Evaluates governance policies to determine if approval is needed,
replacing the hardcoded APPROVAL_REQUIRED_TASK_TYPES set.
"""

import uuid
import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.governance_policy import (
    GovernancePolicy,
    PolicyTrigger,
    PolicyAction,
)

logger = logging.getLogger(__name__)


async def create_policy(
    db: AsyncSession,
    *,
    name: str,
    trigger: PolicyTrigger,
    action: PolicyAction,
    rules: dict | None = None,
    project_id: uuid.UUID | None = None,
    description: str | None = None,
    enabled: bool = True,
    priority: int = 0,
) -> GovernancePolicy:
    """Create a new governance policy."""
    policy = GovernancePolicy(
        name=name,
        description=description,
        trigger=trigger,
        action=action,
        rules=rules,
        project_id=project_id,
        enabled=enabled,
        priority=priority,
    )
    db.add(policy)
    await db.flush()
    return policy


async def list_policies(
    db: AsyncSession,
    *,
    project_id: uuid.UUID | None = None,
    include_global: bool = True,
) -> list[GovernancePolicy]:
    """List governance policies for a project (including global ones)."""
    query = select(GovernancePolicy).where(GovernancePolicy.enabled.is_(True))

    if project_id and include_global:
        query = query.where(
            (GovernancePolicy.project_id == project_id)
            | (GovernancePolicy.project_id.is_(None))
        )
    elif project_id:
        query = query.where(GovernancePolicy.project_id == project_id)
    else:
        query = query.where(GovernancePolicy.project_id.is_(None))

    query = query.order_by(GovernancePolicy.priority.desc())
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_policy(
    db: AsyncSession,
    policy_id: uuid.UUID,
) -> GovernancePolicy | None:
    """Get a single policy by ID."""
    result = await db.execute(
        select(GovernancePolicy).where(GovernancePolicy.id == policy_id)
    )
    return result.scalar_one_or_none()


async def update_policy(
    db: AsyncSession,
    policy_id: uuid.UUID,
    **updates: Any,
) -> GovernancePolicy | None:
    """Update a governance policy."""
    policy = await get_policy(db, policy_id)
    if policy is None:
        return None

    allowed_fields = {
        "name", "description", "trigger", "action",
        "rules", "enabled", "priority",
    }
    for key, value in updates.items():
        if key in allowed_fields and value is not None:
            setattr(policy, key, value)

    await db.flush()
    return policy


async def delete_policy(
    db: AsyncSession,
    policy_id: uuid.UUID,
) -> bool:
    """Delete a governance policy. Returns True if deleted."""
    policy = await get_policy(db, policy_id)
    if policy is None:
        return False
    await db.delete(policy)
    await db.flush()
    return True


async def evaluate_task_approval(
    db: AsyncSession,
    *,
    task_type: str,
    project_id: uuid.UUID,
) -> PolicyAction:
    """Evaluate policies to determine if a task type requires approval.

    Returns the action from the highest-priority matching policy,
    or AUTO_APPROVE if no policy matches.
    """
    policies = await list_policies(db, project_id=project_id)

    for policy in policies:
        if policy.trigger == PolicyTrigger.TASK_TYPE:
            rules = policy.rules or {}
            task_types = rules.get("task_types", [])
            if task_type in task_types:
                logger.info(
                    "Policy '%s' matched task_type '%s' -> %s",
                    policy.name,
                    task_type,
                    policy.action.value,
                )
                return policy.action

    # No matching policy — default to auto-approve
    return PolicyAction.AUTO_APPROVE


async def evaluate_cost_threshold(
    db: AsyncSession,
    *,
    current_cost_usd: float,
    project_id: uuid.UUID,
) -> PolicyAction:
    """Evaluate if current cost exceeds any cost threshold policies."""
    policies = await list_policies(db, project_id=project_id)

    for policy in policies:
        if policy.trigger == PolicyTrigger.COST_THRESHOLD:
            rules = policy.rules or {}
            threshold = rules.get("cost_threshold_usd", float("inf"))
            if current_cost_usd >= threshold:
                logger.info(
                    "Policy '%s' triggered: cost $%.4f >= threshold $%.4f -> %s",
                    policy.name,
                    current_cost_usd,
                    threshold,
                    policy.action.value,
                )
                return policy.action

    return PolicyAction.AUTO_APPROVE


async def seed_default_policies(db: AsyncSession) -> list[GovernancePolicy]:
    """Seed default governance policies (replaces hardcoded approval gates).

    These match the previously hardcoded APPROVAL_REQUIRED_TASK_TYPES.
    """
    existing = await list_policies(db, include_global=True)
    if existing:
        return existing  # Already seeded

    defaults = [
        {
            "name": "Architecture Review Gate",
            "description": "Require approval for architecture tasks",
            "trigger": PolicyTrigger.TASK_TYPE,
            "action": PolicyAction.REQUIRE_APPROVAL,
            "rules": {"task_types": ["architecture"]},
            "priority": 10,
        },
        {
            "name": "Code Review Gate",
            "description": "Require approval for review tasks",
            "trigger": PolicyTrigger.TASK_TYPE,
            "action": PolicyAction.REQUIRE_APPROVAL,
            "rules": {"task_types": ["review"]},
            "priority": 10,
        },
    ]

    created = []
    for d in defaults:
        policy = await create_policy(db, **d)
        created.append(policy)

    return created
