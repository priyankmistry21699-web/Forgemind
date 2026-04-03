"""Design doc synthesis service.

FM-086: Generate architecture/design summaries from the graph,
topology, drift findings, and rule results.
"""

import uuid
from collections import defaultdict
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.architecture import (
    ArchitectureNode,
    ArchitectureEdge,
    ArchitectureDrift,
    ArchitectureRuleResult,
    NodeStatus,
    DriftStatus,
    RuleResultStatus,
)


async def generate_design_doc(
    db: AsyncSession,
    *,
    project_id: uuid.UUID,
) -> dict:
    """Generate a Markdown architecture summary for a project."""

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
        select(ArchitectureEdge).where(ArchitectureEdge.project_id == project_id)
    )
    edges = list(edges_result.scalars().all())

    # Load drift findings
    drifts_result = await db.execute(
        select(ArchitectureDrift).where(
            ArchitectureDrift.project_id == project_id,
            ArchitectureDrift.status == DriftStatus.OPEN,
        )
    )
    drifts = list(drifts_result.scalars().all())

    # Load rule violations
    violations_result = await db.execute(
        select(ArchitectureRuleResult).where(
            ArchitectureRuleResult.project_id == project_id,
            ArchitectureRuleResult.status == RuleResultStatus.VIOLATION,
        )
    )
    violations = list(violations_result.scalars().all())

    # Build document sections
    sections = []
    content_parts = []

    # Header
    content_parts.append("# Architecture Summary\n")
    sections.append("overview")

    # Overview
    content_parts.append("## Overview\n")
    content_parts.append(f"- **Total components:** {len(nodes)}")
    content_parts.append(f"- **Total dependencies:** {len(edges)}")
    content_parts.append(f"- **Open drift findings:** {len(drifts)}")
    content_parts.append(f"- **Rule violations:** {len(violations)}")
    content_parts.append("")

    # Component breakdown by type
    type_counts: dict[str, int] = defaultdict(int)
    for n in nodes:
        type_counts[n.node_type.value] += 1
    if type_counts:
        sections.append("components")
        content_parts.append("## Components by Type\n")
        for t, c in sorted(type_counts.items(), key=lambda x: -x[1]):
            content_parts.append(f"- **{t}:** {c}")
        content_parts.append("")

    # Layer breakdown
    layer_counts: dict[str, int] = defaultdict(int)
    for n in nodes:
        layer = (n.metadata_ or {}).get("layer", "other")
        layer_counts[layer] += 1
    if layer_counts:
        sections.append("layers")
        content_parts.append("## Layers\n")
        for layer, c in sorted(layer_counts.items(), key=lambda x: -x[1]):
            content_parts.append(f"- **{layer}:** {c} module(s)")
        content_parts.append("")

    # Dependency map
    if edges:
        sections.append("dependencies")
        content_parts.append("## Dependency Map\n")
        edge_type_counts: dict[str, int] = defaultdict(int)
        for e in edges:
            edge_type_counts[e.edge_type.value] += 1
        for et, c in sorted(edge_type_counts.items(), key=lambda x: -x[1]):
            content_parts.append(f"- **{et}:** {c} relationship(s)")
        content_parts.append("")

    # Hotspots (high incoming degree)
    if nodes and edges:
        sections.append("hotspots")
        in_degree: dict[uuid.UUID, int] = defaultdict(int)
        for e in edges:
            in_degree[e.to_node_id] += 1
        top = sorted(in_degree.items(), key=lambda x: -x[1])[:10]
        if top:
            content_parts.append("## Hotspots (Most Depended-On)\n")
            for nid, deg in top:
                n = node_map.get(nid)
                label = n.key if n else str(nid)
                content_parts.append(f"- **{label}:** {deg} inbound dependency(ies)")
            content_parts.append("")

    # Drift summary
    if drifts:
        sections.append("drift")
        content_parts.append("## Open Drift Findings\n")
        for d in drifts[:20]:
            content_parts.append(
                f"- [{d.severity.value.upper()}] **{d.title}** — {d.description[:200]}"
            )
        content_parts.append("")

    # Rule violations
    if violations:
        sections.append("violations")
        content_parts.append("## Rule Violations\n")
        for v in violations[:20]:
            content_parts.append(f"- **{v.message}**")
        content_parts.append("")

    content = "\n".join(content_parts)
    return {
        "project_id": str(project_id),
        "title": "Architecture Summary",
        "content": content,
        "sections": sections,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
