"""Architecture rule engine service.

FM-084: Define and evaluate architectural rules against the graph.
Supports import, layer, ownership, dependency, and boundary rules.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.architecture import (
    ArchitectureRule, ArchitectureRuleResult,
    ArchitectureNode, ArchitectureEdge,
    RuleCategory, RuleResultStatus, DriftSeverity, NodeStatus,
)


# ── Rule CRUD ────────────────────────────────────────────────────

async def create_rule(
    db: AsyncSession,
    *,
    project_id: uuid.UUID | None,
    name: str,
    category: RuleCategory,
    rule_config: dict,
    description: str | None = None,
    enabled: bool = True,
    severity: DriftSeverity = DriftSeverity.MEDIUM,
) -> ArchitectureRule:
    rule = ArchitectureRule(
        project_id=project_id,
        name=name,
        description=description,
        category=category,
        rule_config=rule_config,
        enabled=enabled,
        severity=severity,
    )
    db.add(rule)
    await db.flush()
    await db.refresh(rule)
    return rule


async def list_rules(
    db: AsyncSession,
    *,
    project_id: uuid.UUID | None = None,
    category: RuleCategory | None = None,
    limit: int = 100,
    offset: int = 0,
) -> tuple[list[ArchitectureRule], int]:
    query = select(ArchitectureRule)
    if project_id is not None:
        query = query.where(
            (ArchitectureRule.project_id == project_id)
            | (ArchitectureRule.project_id.is_(None))
        )
    if category:
        query = query.where(ArchitectureRule.category == category)

    total = (await db.execute(
        select(sa_func.count()).select_from(query.subquery())
    )).scalar_one()
    result = await db.execute(
        query.order_by(ArchitectureRule.created_at.desc()).offset(offset).limit(limit)
    )
    return list(result.scalars().all()), total


# ── Rule evaluation ──────────────────────────────────────────────

async def evaluate_rule(
    db: AsyncSession,
    rule_id: uuid.UUID,
    project_id: uuid.UUID,
) -> ArchitectureRuleResult:
    """Evaluate a single rule against a project's architecture graph."""
    rule_result = await db.execute(
        select(ArchitectureRule).where(ArchitectureRule.id == rule_id)
    )
    rule = rule_result.scalar_one_or_none()
    if rule is None:
        raise ValueError(f"Rule {rule_id} not found")

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

    # Evaluate by category
    evaluator = _EVALUATORS.get(rule.category)
    if evaluator is None:
        result = ArchitectureRuleResult(
            rule_id=rule_id,
            project_id=project_id,
            status=RuleResultStatus.PASS,
            message=f"No evaluator for category '{rule.category.value}'",
        )
    else:
        result = evaluator(rule, nodes, edges, node_map, project_id)

    db.add(result)
    await db.flush()
    await db.refresh(result)
    return result


async def list_rule_results(
    db: AsyncSession,
    project_id: uuid.UUID,
    *,
    status: RuleResultStatus | None = None,
    limit: int = 100,
    offset: int = 0,
) -> tuple[list[ArchitectureRuleResult], int]:
    query = select(ArchitectureRuleResult).where(
        ArchitectureRuleResult.project_id == project_id
    )
    if status:
        query = query.where(ArchitectureRuleResult.status == status)

    total = (await db.execute(
        select(sa_func.count()).select_from(query.subquery())
    )).scalar_one()
    result = await db.execute(
        query.order_by(ArchitectureRuleResult.evaluated_at.desc()).offset(offset).limit(limit)
    )
    return list(result.scalars().all()), total


# ── Evaluators ───────────────────────────────────────────────────

def _evaluate_import_rule(
    rule: ArchitectureRule,
    nodes: list[ArchitectureNode],
    edges: list[ArchitectureEdge],
    node_map: dict,
    project_id: uuid.UUID,
) -> ArchitectureRuleResult:
    """Check forbidden import patterns.

    rule_config: {
        "forbidden_from": "pattern",  # regex pattern for source
        "forbidden_to": "pattern",    # regex pattern for target
    }
    """
    import re

    config = rule.rule_config
    from_pat = config.get("forbidden_from", "")
    to_pat = config.get("forbidden_to", "")
    violations = []
    violating_edge_ids = []

    for edge in edges:
        if edge.edge_type.value != "imports":
            continue
        from_node = node_map.get(edge.from_node_id)
        to_node = node_map.get(edge.to_node_id)
        if not from_node or not to_node:
            continue

        from_match = re.search(from_pat, from_node.key) if from_pat else True
        to_match = re.search(to_pat, to_node.key) if to_pat else True

        if from_match and to_match:
            violations.append(f"{from_node.key} -> {to_node.key}")
            violating_edge_ids.append(str(edge.id))

    if violations:
        return ArchitectureRuleResult(
            rule_id=rule.id,
            project_id=project_id,
            status=RuleResultStatus.VIOLATION,
            message=f"{len(violations)} forbidden import(s) found: {rule.name}",
            details={"violations": violations[:20]},
            violating_edge_ids=violating_edge_ids[:20],
        )
    return ArchitectureRuleResult(
        rule_id=rule.id,
        project_id=project_id,
        status=RuleResultStatus.PASS,
        message=f"No violations: {rule.name}",
    )


def _evaluate_layer_rule(
    rule: ArchitectureRule,
    nodes: list[ArchitectureNode],
    edges: list[ArchitectureEdge],
    node_map: dict,
    project_id: uuid.UUID,
) -> ArchitectureRuleResult:
    """Check layer boundary violations.

    rule_config: {
        "forbidden_layers": [["model", "api"], ["model", "service"]]
    }
    """
    config = rule.rule_config
    forbidden = [tuple(pair) for pair in config.get("forbidden_layers", [])]
    violations = []
    violating_edge_ids = []

    for edge in edges:
        from_node = node_map.get(edge.from_node_id)
        to_node = node_map.get(edge.to_node_id)
        if not from_node or not to_node:
            continue

        from_layer = (from_node.metadata_ or {}).get("layer", "other")
        to_layer = (to_node.metadata_ or {}).get("layer", "other")

        if (from_layer, to_layer) in forbidden:
            violations.append(f"{from_node.key} ({from_layer}) -> {to_node.key} ({to_layer})")
            violating_edge_ids.append(str(edge.id))

    if violations:
        return ArchitectureRuleResult(
            rule_id=rule.id,
            project_id=project_id,
            status=RuleResultStatus.VIOLATION,
            message=f"{len(violations)} layer violation(s): {rule.name}",
            details={"violations": violations[:20]},
            violating_edge_ids=violating_edge_ids[:20],
        )
    return ArchitectureRuleResult(
        rule_id=rule.id,
        project_id=project_id,
        status=RuleResultStatus.PASS,
        message=f"No violations: {rule.name}",
    )


def _evaluate_dependency_rule(
    rule: ArchitectureRule,
    nodes: list[ArchitectureNode],
    edges: list[ArchitectureEdge],
    node_map: dict,
    project_id: uuid.UUID,
) -> ArchitectureRuleResult:
    """Check forbidden dependency relationships.

    rule_config: {
        "source_pattern": "pattern",   # source node key pattern
        "target_pattern": "pattern",   # target node key pattern
    }
    """
    import re

    config = rule.rule_config
    src_pat = config.get("source_pattern", "")
    tgt_pat = config.get("target_pattern", "")
    violations = []
    violating_edge_ids = []

    for edge in edges:
        if edge.edge_type.value not in ("depends_on", "imports", "calls"):
            continue
        from_node = node_map.get(edge.from_node_id)
        to_node = node_map.get(edge.to_node_id)
        if not from_node or not to_node:
            continue

        src_match = re.search(src_pat, from_node.key) if src_pat else True
        tgt_match = re.search(tgt_pat, to_node.key) if tgt_pat else True

        if src_match and tgt_match:
            violations.append(f"{from_node.key} -> {to_node.key}")
            violating_edge_ids.append(str(edge.id))

    if violations:
        return ArchitectureRuleResult(
            rule_id=rule.id,
            project_id=project_id,
            status=RuleResultStatus.VIOLATION,
            message=f"{len(violations)} forbidden dependency(ies): {rule.name}",
            details={"violations": violations[:20]},
            violating_edge_ids=violating_edge_ids[:20],
        )
    return ArchitectureRuleResult(
        rule_id=rule.id,
        project_id=project_id,
        status=RuleResultStatus.PASS,
        message=f"No violations: {rule.name}",
    )


def _evaluate_boundary_rule(
    rule: ArchitectureRule,
    nodes: list[ArchitectureNode],
    edges: list[ArchitectureEdge],
    node_map: dict,
    project_id: uuid.UUID,
) -> ArchitectureRuleResult:
    """Check that certain modules stay within a boundary.

    rule_config: {
        "boundary_pattern": "pattern",    # nodes that should stay internal
        "allowed_consumers": "pattern",   # who is allowed to import them
    }
    """
    import re

    config = rule.rule_config
    boundary_pat = config.get("boundary_pattern", "")
    allowed_pat = config.get("allowed_consumers", "")
    violations = []
    violating_edge_ids = []

    boundary_node_ids = set()
    for n in nodes:
        if re.search(boundary_pat, n.key):
            boundary_node_ids.add(n.id)

    for edge in edges:
        if edge.to_node_id not in boundary_node_ids:
            continue
        from_node = node_map.get(edge.from_node_id)
        if not from_node:
            continue
        if allowed_pat and re.search(allowed_pat, from_node.key):
            continue
        to_node = node_map.get(edge.to_node_id)
        violations.append(f"{from_node.key} -> {to_node.key if to_node else '?'}")
        violating_edge_ids.append(str(edge.id))

    if violations:
        return ArchitectureRuleResult(
            rule_id=rule.id,
            project_id=project_id,
            status=RuleResultStatus.VIOLATION,
            message=f"{len(violations)} boundary violation(s): {rule.name}",
            details={"violations": violations[:20]},
            violating_edge_ids=violating_edge_ids[:20],
        )
    return ArchitectureRuleResult(
        rule_id=rule.id,
        project_id=project_id,
        status=RuleResultStatus.PASS,
        message=f"No violations: {rule.name}",
    )


def _evaluate_ownership_rule(
    rule: ArchitectureRule,
    nodes: list[ArchitectureNode],
    edges: list[ArchitectureEdge],
    node_map: dict,
    project_id: uuid.UUID,
) -> ArchitectureRuleResult:
    """Check that nodes of a given type have an 'owner' in metadata.

    rule_config: {
        "target_type": "service",   # NodeType value to check (optional, defaults to all)
    }
    """
    config = rule.rule_config
    target_type = config.get("target_type")
    violations = []
    violating_node_ids = []

    for n in nodes:
        # Filter by target type if specified
        if target_type and n.node_type.value != target_type:
            continue
        owner = (n.metadata_ or {}).get("owner")
        if not owner:
            violations.append(f"{n.key} ({n.node_type.value}) has no owner")
            violating_node_ids.append(str(n.id))

    if violations:
        return ArchitectureRuleResult(
            rule_id=rule.id,
            project_id=project_id,
            status=RuleResultStatus.VIOLATION,
            message=f"{len(violations)} unowned component(s): {rule.name}",
            details={"violations": violations[:20]},
            violating_node_ids=violating_node_ids[:20],
        )
    return ArchitectureRuleResult(
        rule_id=rule.id,
        project_id=project_id,
        status=RuleResultStatus.PASS,
        message=f"No violations: {rule.name}",
    )


_EVALUATORS = {
    RuleCategory.IMPORT: _evaluate_import_rule,
    RuleCategory.LAYER: _evaluate_layer_rule,
    RuleCategory.DEPENDENCY: _evaluate_dependency_rule,
    RuleCategory.BOUNDARY: _evaluate_boundary_rule,
    RuleCategory.OWNERSHIP: _evaluate_ownership_rule,
}
