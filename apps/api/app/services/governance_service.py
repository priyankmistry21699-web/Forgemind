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
    run_id: uuid.UUID | None = None,
    cost_usd: float | None = None,
    agent_slug: str | None = None,
    artifact_type: str | None = None,
) -> PolicyAction:
    """Evaluate policies to determine if a task type requires approval.

    FM-047: Enhanced evaluation with multi-trigger support:
    - TASK_TYPE: matches task type against policy rules
    - COST_THRESHOLD: matches when run cost exceeds threshold
    - ARTIFACT_TYPE: matches artifact type
    - AGENT_ACTION: matches specific agent slug
    - CUSTOM: matches custom JSON conditions

    Returns the action from the highest-priority matching policy,
    or AUTO_APPROVE if no policy matches.
    """
    policies = await list_policies(db, project_id=project_id)

    for policy in policies:
        if _policy_matches(policy, task_type=task_type, cost_usd=cost_usd,
                           agent_slug=agent_slug, artifact_type=artifact_type):
            logger.info(
                "Policy '%s' (trigger=%s) matched -> %s",
                policy.name,
                policy.trigger.value,
                policy.action.value,
            )
            return policy.action

    # No matching policy — default to auto-approve
    return PolicyAction.AUTO_APPROVE


def _policy_matches(
    policy: GovernancePolicy,
    *,
    task_type: str | None = None,
    cost_usd: float | None = None,
    agent_slug: str | None = None,
    artifact_type: str | None = None,
) -> bool:
    """Check if a policy matches the given context."""
    rules = policy.rules or {}

    if policy.trigger == PolicyTrigger.TASK_TYPE:
        task_types = rules.get("task_types", [])
        return task_type in task_types

    elif policy.trigger == PolicyTrigger.COST_THRESHOLD:
        threshold = rules.get("threshold_usd", 0.0)
        return cost_usd is not None and cost_usd > threshold

    elif policy.trigger == PolicyTrigger.ARTIFACT_TYPE:
        artifact_types = rules.get("artifact_types", [])
        return artifact_type in artifact_types

    elif policy.trigger == PolicyTrigger.AGENT_ACTION:
        agent_slugs = rules.get("agent_slugs", [])
        return agent_slug in agent_slugs

    elif policy.trigger == PolicyTrigger.CUSTOM:
        # Custom conditions evaluated from rules JSON
        return _evaluate_custom_rules(rules, task_type=task_type,
                                      cost_usd=cost_usd, agent_slug=agent_slug)

    return False


def _evaluate_custom_rules(
    rules: dict,
    *,
    task_type: str | None = None,
    cost_usd: float | None = None,
    agent_slug: str | None = None,
) -> bool:
    """Evaluate custom rule conditions.

    Supports simple condition objects:
    {
        "conditions": [
            {"field": "task_type", "op": "in", "value": ["architecture"]},
            {"field": "cost_usd", "op": "gt", "value": 1.0}
        ],
        "logic": "and"  // or "or"
    }
    """
    conditions = rules.get("conditions", [])
    logic = rules.get("logic", "and")

    if not conditions:
        return False

    context = {
        "task_type": task_type,
        "cost_usd": cost_usd,
        "agent_slug": agent_slug,
    }

    results = []
    for cond in conditions:
        field = cond.get("field", "")
        op = cond.get("op", "eq")
        value = cond.get("value")
        field_val = context.get(field)

        if op == "eq":
            results.append(field_val == value)
        elif op == "ne":
            results.append(field_val != value)
        elif op == "in":
            results.append(field_val in (value or []))
        elif op == "gt" and field_val is not None:
            results.append(field_val > value)
        elif op == "lt" and field_val is not None:
            results.append(field_val < value)
        elif op == "gte" and field_val is not None:
            results.append(field_val >= value)
        elif op == "lte" and field_val is not None:
            results.append(field_val <= value)
        else:
            results.append(False)

    if logic == "or":
        return any(results)
    return all(results)


async def evaluate_approval_with_council(
    db: AsyncSession,
    *,
    task_type: str,
    project_id: uuid.UUID,
    run_id: uuid.UUID | None = None,
    cost_usd: float | None = None,
    agent_slug: str | None = None,
) -> dict:
    """Enhanced approval evaluation that considers council decisions.

    FM-047: Returns action with explanation and whether council is needed.
    """
    action = await evaluate_task_approval(
        db,
        task_type=task_type,
        project_id=project_id,
        run_id=run_id,
        cost_usd=cost_usd,
        agent_slug=agent_slug,
    )

    needs_council = False
    # If action is REQUIRE_APPROVAL and there are cost concerns, suggest council
    if action == PolicyAction.REQUIRE_APPROVAL and cost_usd is not None and cost_usd > 0.5:
        needs_council = True

    return {
        "action": action.value,
        "needs_council": needs_council,
        "task_type": task_type,
        "project_id": str(project_id),
        "explanation": f"Policy evaluation: {action.value}"
                       + (" (council recommended)" if needs_council else ""),
    }



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
