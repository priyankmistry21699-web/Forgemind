"""Impact analysis service.

FM-087: Traverse the architecture graph from a target node to compute
blast-radius, impacted services, and an overall severity score.
"""

import uuid
from collections import deque

from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.architecture import (
    ArchitectureNode, ArchitectureEdge, ChangeImpactAssessment,
    NodeType, ImpactSeverity,
)


async def analyse_impact(
    db: AsyncSession,
    *,
    project_id: uuid.UUID,
    node_id: uuid.UUID | None = None,
    file_path: str | None = None,
    module_key: str | None = None,
) -> ChangeImpactAssessment:
    """Run impact analysis for a target node / path / key."""

    # Resolve target node
    target_node = None
    if node_id:
        target_node = await db.get(ArchitectureNode, node_id)
    elif file_path:
        result = await db.execute(
            select(ArchitectureNode).where(
                ArchitectureNode.project_id == project_id,
                ArchitectureNode.path == file_path,
            ).limit(1)
        )
        target_node = result.scalars().first()
    elif module_key:
        result = await db.execute(
            select(ArchitectureNode).where(
                ArchitectureNode.project_id == project_id,
                ArchitectureNode.key == module_key,
            ).limit(1)
        )
        target_node = result.scalars().first()

    if target_node is None:
        # Create assessment even when node is not mapped
        assessment = ChangeImpactAssessment(
            project_id=project_id,
            target_path=file_path,
            target_key=module_key,
            severity=ImpactSeverity.LOW,
            blast_radius=0,
            impacted_nodes=[],
            impacted_services=[],
            rationale="Target not found in architecture graph.",
            confidence_score=0.2,
        )
        db.add(assessment)
        await db.flush()
        return assessment

    # BFS reverse traversal (who depends on the target?)
    edges_result = await db.execute(
        select(ArchitectureEdge).where(
            ArchitectureEdge.project_id == project_id
        )
    )
    all_edges = list(edges_result.scalars().all())

    # Build reverse adjacency: to_node_id -> list of from_node_ids
    reverse_adj: dict[uuid.UUID, list[uuid.UUID]] = {}
    for e in all_edges:
        reverse_adj.setdefault(e.to_node_id, []).append(e.from_node_id)

    visited: set[uuid.UUID] = set()
    queue: deque[uuid.UUID] = deque([target_node.id])
    visited.add(target_node.id)

    while queue:
        current = queue.popleft()
        for dep_id in reverse_adj.get(current, []):
            if dep_id not in visited:
                visited.add(dep_id)
                queue.append(dep_id)

    # Remove self
    visited.discard(target_node.id)
    blast_radius = len(visited)

    # Load impacted nodes for metadata
    impacted_node_ids = [str(nid) for nid in visited]
    impacted_services: list[str] = []

    if visited:
        svc_result = await db.execute(
            select(ArchitectureNode).where(
                ArchitectureNode.id.in_(list(visited)),
                ArchitectureNode.node_type == NodeType.SERVICE,
            )
        )
        impacted_services = [n.key for n in svc_result.scalars().all()]

    # Score severity by blast radius
    if blast_radius >= 20:
        severity = ImpactSeverity.CRITICAL
    elif blast_radius >= 10:
        severity = ImpactSeverity.HIGH
    elif blast_radius >= 3:
        severity = ImpactSeverity.MEDIUM
    else:
        severity = ImpactSeverity.LOW

    confidence = min(1.0, 0.5 + 0.02 * len(all_edges))

    rationale_parts = [
        f"Changing '{target_node.key}' impacts {blast_radius} downstream component(s).",
    ]
    if impacted_services:
        rationale_parts.append(f"Affected services: {', '.join(impacted_services)}.")

    assessment = ChangeImpactAssessment(
        project_id=project_id,
        target_node_id=target_node.id,
        target_path=target_node.path,
        target_key=target_node.key,
        severity=severity,
        blast_radius=blast_radius,
        impacted_nodes=impacted_node_ids,
        impacted_services=impacted_services,
        rationale=" ".join(rationale_parts),
        confidence_score=round(confidence, 2),
    )
    db.add(assessment)
    await db.flush()
    return assessment
