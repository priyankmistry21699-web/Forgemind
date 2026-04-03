"""Refactor recommendation service.

FM-088: Analyse the architecture graph, drift findings, and rule
violations to produce actionable refactoring suggestions.
"""

import uuid
from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.architecture import (
    ArchitectureNode, ArchitectureEdge, ArchitectureDrift,
    ArchitectureRuleResult, NodeStatus, DriftStatus, DriftSeverity,
    RuleResultStatus, NodeType,
)


async def generate_recommendations(
    db: AsyncSession,
    *,
    project_id: uuid.UUID,
) -> list[dict]:
    """Generate refactoring recommendations based on graph analysis."""

    recommendations: list[dict] = []

    # Load graph
    nodes_result = await db.execute(
        select(ArchitectureNode).where(
            ArchitectureNode.project_id == project_id,
            ArchitectureNode.status == NodeStatus.ACTIVE,
        )
    )
    nodes = list(nodes_result.scalars().all())
    node_map = {n.id: n for n in nodes}

    edges_result = await db.execute(
        select(ArchitectureEdge).where(
            ArchitectureEdge.project_id == project_id
        )
    )
    edges = list(edges_result.scalars().all())

    # 1. High fan-in detection (God-module smell)
    in_degree: dict[uuid.UUID, int] = defaultdict(int)
    out_degree: dict[uuid.UUID, int] = defaultdict(int)
    for e in edges:
        in_degree[e.to_node_id] += 1
        out_degree[e.from_node_id] += 1

    threshold_fanin = max(5, len(nodes) // 5) if nodes else 5
    for nid, deg in in_degree.items():
        if deg >= threshold_fanin:
            n = node_map.get(nid)
            if n:
                recommendations.append({
                    "recommendation_type": "decompose_god_module",
                    "title": f"Decompose high-fanin module '{n.key}'",
                    "description": (
                        f"Module '{n.key}' has {deg} inbound dependencies, "
                        f"making it a change-risk hotspot. Consider splitting "
                        f"into smaller, focused modules."
                    ),
                    "severity": DriftSeverity.HIGH.value,
                    "confidence": round(min(1.0, deg / (threshold_fanin * 2)), 2),
                    "affected_nodes": [n.key],
                    "rationale": f"Fan-in of {deg} exceeds threshold of {threshold_fanin}.",
                })

    # 2. Circular dependency detection (simple: mutual edges)
    edge_set = {(e.from_node_id, e.to_node_id) for e in edges}
    seen_pairs: set[tuple[uuid.UUID, uuid.UUID]] = set()
    for a, b in edge_set:
        if (b, a) in edge_set and (b, a) not in seen_pairs:
            seen_pairs.add((a, b))
            na = node_map.get(a)
            nb = node_map.get(b)
            if na and nb:
                recommendations.append({
                    "recommendation_type": "break_circular_dependency",
                    "title": f"Break circular dependency: {na.key} <-> {nb.key}",
                    "description": (
                        f"'{na.key}' and '{nb.key}' depend on each other. "
                        f"Introduce an interface or event to decouple them."
                    ),
                    "severity": DriftSeverity.MEDIUM.value,
                    "confidence": 0.9,
                    "affected_nodes": [na.key, nb.key],
                    "rationale": "Mutual dependency detected between the two modules.",
                })

    # 3. Isolated nodes (zero edges)
    connected = set()
    for e in edges:
        connected.add(e.from_node_id)
        connected.add(e.to_node_id)
    for n in nodes:
        if n.id not in connected and n.node_type not in (
            NodeType.WORKSPACE, NodeType.PROJECT, NodeType.REPOSITORY
        ):
            recommendations.append({
                "recommendation_type": "remove_or_integrate_isolated",
                "title": f"Integrate or remove isolated module '{n.key}'",
                "description": (
                    f"Module '{n.key}' has no connections to other components. "
                    f"It may be dead code or missing dependency declarations."
                ),
                "severity": DriftSeverity.LOW.value,
                "confidence": 0.6,
                "affected_nodes": [n.key],
                "rationale": "Zero inbound or outbound edges.",
            })

    # 4. Drift-driven recommendations
    drifts_result = await db.execute(
        select(ArchitectureDrift).where(
            ArchitectureDrift.project_id == project_id,
            ArchitectureDrift.status == DriftStatus.OPEN,
        )
    )
    drifts = list(drifts_result.scalars().all())
    if len(drifts) >= 3:
        recommendations.append({
            "recommendation_type": "address_drift_backlog",
            "title": f"Address {len(drifts)} open drift finding(s)",
            "description": (
                f"There are {len(drifts)} unresolved drift findings. "
                f"Prioritise high-severity items to reduce architectural debt."
            ),
            "severity": DriftSeverity.HIGH.value if any(
                d.severity in (DriftSeverity.HIGH, DriftSeverity.CRITICAL)
                for d in drifts
            ) else DriftSeverity.MEDIUM.value,
            "confidence": 0.85,
            "affected_nodes": [d.title for d in drifts[:10]],
            "rationale": f"{len(drifts)} open drift findings detected.",
        })

    # 5. Rule-violation-driven recommendations
    violations_result = await db.execute(
        select(ArchitectureRuleResult).where(
            ArchitectureRuleResult.project_id == project_id,
            ArchitectureRuleResult.status == RuleResultStatus.VIOLATION,
        )
    )
    violations = list(violations_result.scalars().all())
    if violations:
        recommendations.append({
            "recommendation_type": "fix_rule_violations",
            "title": f"Fix {len(violations)} architectural rule violation(s)",
            "description": (
                f"{len(violations)} rule evaluations resulted in violations. "
                f"Review and remediate to keep the architecture compliant."
            ),
            "severity": DriftSeverity.HIGH.value,
            "confidence": 0.9,
            "affected_nodes": [v.message[:80] for v in violations[:10]],
            "rationale": f"{len(violations)} rule violation(s) found.",
        })

    return recommendations
