"""Structural health score service.

FM-090: Compute a per-project health score that aggregates drift findings,
rule compliance, component coverage, and isolated-node ratios into a
single 0-100 score with breakdowns.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.architecture import (
    ArchitectureNode,
    ArchitectureEdge,
    ArchitectureDrift,
    ArchitectureRuleResult,
    NodeStatus,
    DriftStatus,
    DriftSeverity,
    RuleResultStatus,
)


# ── Severity weights for drift penalty ───────────────────────────
_DRIFT_WEIGHTS: dict[DriftSeverity, float] = {
    DriftSeverity.CRITICAL: 10.0,
    DriftSeverity.HIGH: 5.0,
    DriftSeverity.MEDIUM: 2.0,
    DriftSeverity.LOW: 0.5,
}


async def compute_health_score(
    db: AsyncSession,
    *,
    project_id: uuid.UUID,
) -> dict:
    """Return a structural health score dict for the project.

    Returns:
        {
            "project_id": str,
            "overall_score": float (0-100),
            "component_coverage": float (0-100),
            "drift_penalty": float (0+),
            "rule_compliance": float (0-100),
            "isolation_ratio": float (0-100),
            "details": { ... }
        }
    """

    # ── Load graph ───────────────────────────────────────────────
    nodes_result = await db.execute(
        select(ArchitectureNode).where(
            ArchitectureNode.project_id == project_id,
            ArchitectureNode.status == NodeStatus.ACTIVE,
        )
    )
    nodes = list(nodes_result.scalars().all())

    edges_result = await db.execute(
        select(ArchitectureEdge).where(
            ArchitectureEdge.project_id == project_id,
        )
    )
    edges = list(edges_result.scalars().all())

    # ── Load open drifts ─────────────────────────────────────────
    drifts_result = await db.execute(
        select(ArchitectureDrift).where(
            ArchitectureDrift.project_id == project_id,
            ArchitectureDrift.status == DriftStatus.OPEN,
        )
    )
    open_drifts = list(drifts_result.scalars().all())

    # ── Load rule results ────────────────────────────────────────
    results_result = await db.execute(
        select(ArchitectureRuleResult).where(
            ArchitectureRuleResult.project_id == project_id,
        )
    )
    all_results = list(results_result.scalars().all())

    # ── 1. Component coverage ────────────────────────────────────
    # Ratio of nodes that have documentation (declared source type)
    declared_count = sum(1 for n in nodes if n.source_type.value == "declared")
    component_coverage = (declared_count / len(nodes) * 100) if nodes else 100.0

    # ── 2. Drift penalty ─────────────────────────────────────────
    drift_penalty = sum(_DRIFT_WEIGHTS.get(d.severity, 1.0) for d in open_drifts)

    # ── 3. Rule compliance ───────────────────────────────────────
    total_evals = len(all_results)
    violations = sum(1 for r in all_results if r.status == RuleResultStatus.VIOLATION)
    rule_compliance = (
        ((total_evals - violations) / total_evals * 100) if total_evals > 0 else 100.0
    )

    # ── 4. Isolation ratio ───────────────────────────────────────
    connected_ids: set[uuid.UUID] = set()
    for e in edges:
        connected_ids.add(e.from_node_id)
        connected_ids.add(e.to_node_id)
    isolated_count = sum(1 for n in nodes if n.id not in connected_ids)
    isolation_ratio = (
        ((len(nodes) - isolated_count) / len(nodes) * 100) if nodes else 100.0
    )

    # ── Composite score ──────────────────────────────────────────
    # Weighted average: coverage 20%, compliance 30%, isolation 10%, drift deductions
    base_score = (
        component_coverage * 0.20
        + rule_compliance * 0.30
        + isolation_ratio * 0.10
        + 40.0  # remaining 40% is a baseline that drifts erode
    )
    overall = max(0.0, min(100.0, base_score - drift_penalty))

    return {
        "project_id": str(project_id),
        "overall_score": round(overall, 1),
        "component_coverage": round(component_coverage, 1),
        "drift_penalty": round(drift_penalty, 1),
        "rule_compliance": round(rule_compliance, 1),
        "isolation_ratio": round(isolation_ratio, 1),
        "details": {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "declared_nodes": declared_count,
            "open_drifts": len(open_drifts),
            "total_rule_evaluations": total_evals,
            "rule_violations": violations,
            "isolated_nodes": isolated_count,
        },
    }
