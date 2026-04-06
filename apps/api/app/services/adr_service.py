"""FM-107: ADR-aware planning pipeline.

Generates Architecture Decision Record (ADR) sections and enriches
PLAN artifacts with architecture context from the project's graph,
drift findings, and structural health data.
"""

import uuid
import logging

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
    DriftSeverity,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# ADR section generation
# ---------------------------------------------------------------------------


async def build_adr_section(
    db: AsyncSession,
    *,
    project_id: uuid.UUID,
    spec_content: str | None = None,
) -> str | None:
    """Build an ADR-style markdown section from current architecture state.

    Returns None if the project has no architecture data.
    """
    # Load active nodes
    nodes_result = await db.execute(
        select(ArchitectureNode).where(
            ArchitectureNode.project_id == project_id,
            ArchitectureNode.status == NodeStatus.ACTIVE,
        )
    )
    nodes = list(nodes_result.scalars().all())
    if not nodes:
        return None

    # Load edges
    edges_result = await db.execute(
        select(ArchitectureEdge).where(
            ArchitectureEdge.project_id == project_id
        )
    )
    edges = list(edges_result.scalars().all())
    node_map = {n.id: n for n in nodes}

    # Load open drifts
    drifts_result = await db.execute(
        select(ArchitectureDrift).where(
            ArchitectureDrift.project_id == project_id,
            ArchitectureDrift.status == DriftStatus.OPEN,
        )
    )
    drifts = list(drifts_result.scalars().all())

    # Load failed rule results
    rule_results = await db.execute(
        select(ArchitectureRuleResult).where(
            ArchitectureRuleResult.project_id == project_id,
            ArchitectureRuleResult.status == RuleResultStatus.VIOLATION,
        )
    )
    violations = list(rule_results.scalars().all())

    return _format_adr_section(nodes, edges, drifts, violations, node_map)


async def enrich_plan_with_adr(
    db: AsyncSession,
    *,
    project_id: uuid.UUID,
    plan_content: str,
    spec_content: str | None = None,
) -> str:
    """Append ADR section to plan content if architecture data exists."""
    adr = await build_adr_section(
        db, project_id=project_id, spec_content=spec_content
    )
    if adr is None:
        return plan_content
    return f"{plan_content}\n\n{adr}"


async def get_architecture_context_for_prompt(
    db: AsyncSession,
    project_id: uuid.UUID,
) -> str | None:
    """Build a concise architecture summary suitable for LLM prompts.

    Returns a short markdown section describing the current architecture
    state, or None if no architecture data exists.
    """
    nodes_result = await db.execute(
        select(ArchitectureNode).where(
            ArchitectureNode.project_id == project_id,
            ArchitectureNode.status == NodeStatus.ACTIVE,
        )
    )
    nodes = list(nodes_result.scalars().all())
    if not nodes:
        return None

    edges_result = await db.execute(
        select(ArchitectureEdge).where(
            ArchitectureEdge.project_id == project_id
        )
    )
    edges = list(edges_result.scalars().all())
    node_map = {n.id: n for n in nodes}

    lines = [
        "## Current Architecture Context",
        f"Components: {len(nodes)} active",
        f"Dependencies: {len(edges)} edges",
        "",
        "### Components",
    ]
    for n in nodes[:20]:  # Cap to avoid prompt bloat
        lines.append(f"- **{n.name}** ({n.node_type.value}): {n.path or 'No description'}")

    if len(nodes) > 20:
        lines.append(f"- ... and {len(nodes) - 20} more")

    lines.append("")
    lines.append("### Key Dependencies")
    for e in edges[:15]:
        src = node_map.get(e.from_node_id)
        tgt = node_map.get(e.to_node_id)
        if src and tgt:
            lines.append(f"- {src.name} → {tgt.name} ({e.edge_type.value})")

    if len(edges) > 15:
        lines.append(f"- ... and {len(edges) - 15} more")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------


def _format_adr_section(
    nodes: list,
    edges: list,
    drifts: list,
    violations: list,
    node_map: dict,
) -> str:
    """Format ADR-style markdown section."""
    lines = [
        "---",
        "",
        "# Architecture Decision Records",
        "",
        "## ADR-001: Current Architecture State",
        "",
        "### Context",
        f"The project has {len(nodes)} active components with {len(edges)} dependencies.",
        "",
        "### Decision",
        "Plan should account for the following architectural considerations:",
        "",
    ]

    # Component summary
    by_type: dict[str, int] = {}
    for n in nodes:
        by_type[n.node_type.value] = by_type.get(n.node_type.value, 0) + 1
    for ntype, count in sorted(by_type.items()):
        lines.append(f"- {count} {ntype}(s)")

    # Open drifts
    if drifts:
        lines.extend([
            "",
            "## ADR-002: Active Drift Findings",
            "",
            "### Context",
            f"{len(drifts)} open drift findings must be considered during planning.",
            "",
            "### Details",
        ])
        high_drifts = [d for d in drifts if d.severity == DriftSeverity.HIGH]
        medium_drifts = [d for d in drifts if d.severity == DriftSeverity.MEDIUM]
        if high_drifts:
            lines.append(f"- **{len(high_drifts)} HIGH severity** drifts")
            for d in high_drifts[:5]:
                lines.append(f"  - {d.description}")
        if medium_drifts:
            lines.append(f"- **{len(medium_drifts)} MEDIUM severity** drifts")
        lines.extend([
            "",
            "### Consequences",
            "- Plan should address or acknowledge these drifts",
            "- High severity drifts may block implementation",
        ])

    # Rule violations
    if violations:
        lines.extend([
            "",
            "## ADR-003: Active Rule Violations",
            "",
            "### Context",
            f"{len(violations)} architecture rules are currently failing.",
            "",
            "### Consequences",
            "- Plan phases should include steps to resolve violations",
            "- Implementation should not introduce new violations",
        ])

    if not drifts and not violations:
        lines.extend([
            "",
            "### Alternatives",
            "- No active drifts or violations — architecture is healthy",
            "",
            "### Consequences",
            "- Plan can proceed with standard implementation approach",
        ])

    return "\n".join(lines)
