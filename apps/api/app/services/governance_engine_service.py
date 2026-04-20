"""Governance engine service — policy evaluation with enforcement.

FM-174: Evaluates governance policies before actions, records results,
and can block or warn based on policy configuration.
Extends the existing GovernancePolicy model (FM-048).
"""

import logging
import uuid
from datetime import datetime

from sqlalchemy import select, func as sa_func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.governance_policy import GovernancePolicy, PolicyAction
from app.models.enterprise_governance import (
    GovernancePolicyEvaluation,
    PolicyEvalResult,
)

logger = logging.getLogger(__name__)


async def evaluate_policies(
    db: AsyncSession,
    *,
    project_id: uuid.UUID,
    trigger_action: str,
    resource_type: str,
    resource_id: uuid.UUID | None = None,
    actor_id: uuid.UUID | None = None,
    context: dict | None = None,
) -> dict:
    """Evaluate all applicable governance policies for a proposed action.

    Returns a dict with:
      - allowed: bool (True if no BLOCK policy matched)
      - evaluations: list of GovernancePolicyEvaluation records
      - blocked_by: list of policy names that blocked the action
      - warnings: list of policy names that warned
    """
    # Find applicable policies: project-specific + global (project_id IS NULL)
    q = (
        select(GovernancePolicy)
        .where(
            GovernancePolicy.enabled == True,  # noqa: E712
            (GovernancePolicy.project_id == project_id)
            | (GovernancePolicy.project_id.is_(None)),
        )
        .order_by(GovernancePolicy.priority.desc())
    )
    policies = (await db.execute(q)).scalars().all()

    evaluations = []
    blocked_by = []
    warnings = []

    for policy in policies:
        result, details = _evaluate_single_policy(
            policy, trigger_action, resource_type, context
        )

        enforced = (
            result == PolicyEvalResult.FAIL and policy.action == PolicyAction.BLOCK
        )

        eval_record = GovernancePolicyEvaluation(
            policy_id=policy.id,
            trigger_action=trigger_action,
            resource_type=resource_type,
            resource_id=resource_id,
            project_id=project_id,
            actor_id=actor_id,
            result=result,
            details=details,
            enforced=enforced,
        )
        db.add(eval_record)
        evaluations.append(eval_record)

        if result == PolicyEvalResult.FAIL:
            if policy.action == PolicyAction.BLOCK:
                blocked_by.append(policy.name)
            elif policy.action == PolicyAction.NOTIFY:
                warnings.append(policy.name)
        elif result == PolicyEvalResult.WARN:
            warnings.append(policy.name)

    await db.flush()

    allowed = len(blocked_by) == 0

    logger.info(
        "policy_eval: project=%s action=%s policies_checked=%d allowed=%s blocked=%s",
        project_id,
        trigger_action,
        len(policies),
        allowed,
        blocked_by,
    )

    return {
        "allowed": allowed,
        "evaluations": evaluations,
        "blocked_by": blocked_by,
        "warnings": warnings,
    }


def _evaluate_single_policy(
    policy: GovernancePolicy,
    trigger_action: str,
    resource_type: str,
    context: dict | None,
) -> tuple[PolicyEvalResult, dict]:
    """Evaluate one policy against the proposed action.

    Returns (result, details_dict).
    """
    rules = policy.rules or {}
    details: dict = {"policy_name": policy.name, "trigger": policy.trigger.value}

    # Match by trigger type
    if policy.trigger.value == "task_type":
        expected_types = rules.get("task_types", [])
        ctx_task_type = (context or {}).get("task_type", "")
        if ctx_task_type in expected_types:
            details["matched"] = True
            details["reason"] = f"Task type '{ctx_task_type}' matches policy"
            return PolicyEvalResult.FAIL, details
        details["matched"] = False
        return PolicyEvalResult.PASS, details

    elif policy.trigger.value == "cost_threshold":
        threshold = rules.get("cost_threshold_usd", 0)
        current_cost = (context or {}).get("estimated_cost_usd", 0)
        if current_cost > threshold:
            details["matched"] = True
            details["reason"] = (
                f"Cost ${current_cost:.2f} exceeds threshold ${threshold:.2f}"
            )
            return PolicyEvalResult.FAIL, details
        details["matched"] = False
        return PolicyEvalResult.PASS, details

    elif policy.trigger.value == "artifact_type":
        expected_types = rules.get("artifact_types", [])
        ctx_artifact_type = (context or {}).get("artifact_type", "")
        if ctx_artifact_type in expected_types:
            details["matched"] = True
            details["reason"] = f"Artifact type '{ctx_artifact_type}' matches policy"
            return PolicyEvalResult.FAIL, details
        details["matched"] = False
        return PolicyEvalResult.PASS, details

    elif policy.trigger.value == "agent_action":
        expected_actions = rules.get("agent_actions", [])
        if trigger_action in expected_actions:
            details["matched"] = True
            details["reason"] = f"Action '{trigger_action}' matches policy"
            return PolicyEvalResult.FAIL, details
        details["matched"] = False
        return PolicyEvalResult.PASS, details

    elif policy.trigger.value == "custom":
        # Custom rules: check resource_type match + any condition keys
        expected_resource = rules.get("resource_type")
        if expected_resource and expected_resource == resource_type:
            details["matched"] = True
            details["reason"] = f"Resource type '{resource_type}' matches custom rule"
            return PolicyEvalResult.FAIL, details
        expected_actions = rules.get("actions", [])
        if trigger_action in expected_actions:
            details["matched"] = True
            details["reason"] = f"Action '{trigger_action}' matches custom rule"
            return PolicyEvalResult.FAIL, details
        details["matched"] = False
        return PolicyEvalResult.PASS, details

    # Unknown trigger — skip
    details["matched"] = False
    details["reason"] = f"Unknown trigger type: {policy.trigger.value}"
    return PolicyEvalResult.SKIP, details


async def list_evaluations(
    db: AsyncSession,
    *,
    project_id: uuid.UUID | None = None,
    workspace_id: uuid.UUID | None = None,
    policy_id: uuid.UUID | None = None,
    result_filter: PolicyEvalResult | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    offset: int = 0,
    limit: int = 50,
) -> tuple[list[GovernancePolicyEvaluation], int]:
    """List policy evaluation records with filters."""
    conditions = []

    if project_id:
        conditions.append(GovernancePolicyEvaluation.project_id == project_id)
    if policy_id:
        conditions.append(GovernancePolicyEvaluation.policy_id == policy_id)
    if result_filter:
        conditions.append(GovernancePolicyEvaluation.result == result_filter)
    if date_from:
        conditions.append(GovernancePolicyEvaluation.created_at >= date_from)
    if date_to:
        conditions.append(GovernancePolicyEvaluation.created_at <= date_to)

    # If workspace_id filter, join through GovernancePolicy → project → workspace
    # For simplicity, filter by project_id in the evaluation table
    if workspace_id and not project_id:
        # Get evaluations where project belongs to workspace
        from app.models.project import Project

        sub = select(Project.id).where(Project.workspace_id == workspace_id)
        conditions.append(
            GovernancePolicyEvaluation.project_id.in_(sub)
            | GovernancePolicyEvaluation.project_id.is_(None)
        )

    where_clause = and_(*conditions) if conditions else True

    count_q = (
        select(sa_func.count())
        .select_from(GovernancePolicyEvaluation)
        .where(where_clause)
    )
    total = (await db.execute(count_q)).scalar() or 0

    items_q = (
        select(GovernancePolicyEvaluation)
        .where(where_clause)
        .order_by(GovernancePolicyEvaluation.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    rows = (await db.execute(items_q)).scalars().all()

    return list(rows), total
