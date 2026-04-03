"""Drift detection service - compare expected vs actual architecture.

FM-083: Detects drift between intended and inferred architecture,
compares snapshots, and manages drift lifecycle.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.architecture import (
    ArchitectureDrift,
    ArchitectureSnapshot,
    ArchitectureNode,
    ArchitectureEdge,
    DriftSeverity,
    DriftStatus,
    NodeStatus,
)


async def detect_drift(
    db: AsyncSession,
    *,
    project_id: uuid.UUID,
    snapshot_id: uuid.UUID | None = None,
) -> list[ArchitectureDrift]:
    """Detect drift by comparing current graph against a snapshot or conventions.

    If snapshot_id is provided, compare current graph vs snapshot.
    Otherwise, apply convention-based checks (cross-layer imports, etc.).
    """
    drifts: list[ArchitectureDrift] = []

    # Load current nodes and edges
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

    if snapshot_id:
        # Snapshot comparison drift
        snap_drifts = await _compare_with_snapshot(
            db, project_id, snapshot_id, nodes, edges, node_map
        )
        drifts.extend(snap_drifts)
    else:
        # Convention-based drift
        conv_drifts = _detect_convention_drift(nodes, edges, node_map)
        for d in conv_drifts:
            drift = ArchitectureDrift(
                project_id=project_id,
                drift_type=d["drift_type"],
                severity=d["severity"],
                title=d["title"],
                description=d["description"],
                source_snapshot_id=snapshot_id,
                metadata_=d.get("metadata_"),
            )
            db.add(drift)
            await db.flush()
            await db.refresh(drift)
            drifts.append(drift)

    return drifts


async def _compare_with_snapshot(
    db: AsyncSession,
    project_id: uuid.UUID,
    snapshot_id: uuid.UUID,
    current_nodes: list[ArchitectureNode],
    current_edges: list[ArchitectureEdge],
    node_map: dict,
) -> list[ArchitectureDrift]:
    """Compare current graph against a saved snapshot."""
    snap_result = await db.execute(
        select(ArchitectureSnapshot).where(ArchitectureSnapshot.id == snapshot_id)
    )
    snap = snap_result.scalar_one_or_none()
    if snap is None or snap.snapshot_data is None:
        return []

    drifts: list[ArchitectureDrift] = []
    snap_data = snap.snapshot_data
    snap_node_keys = {n["key"] for n in snap_data.get("nodes", [])}
    current_node_keys = {n.key for n in current_nodes}

    # New nodes not in snapshot
    new_keys = current_node_keys - snap_node_keys
    if new_keys:
        drift = ArchitectureDrift(
            project_id=project_id,
            drift_type="new_component",
            severity=DriftSeverity.LOW,
            title=f"{len(new_keys)} new component(s) since snapshot",
            description=f"Components added since '{snap.name}': {', '.join(sorted(list(new_keys)[:10]))}",
            source_snapshot_id=snapshot_id,
            comparison_target=snap.name,
            metadata_={"new_keys": sorted(list(new_keys)[:50])},
        )
        db.add(drift)
        await db.flush()
        await db.refresh(drift)
        drifts.append(drift)

    # Removed nodes
    removed_keys = snap_node_keys - current_node_keys
    if removed_keys:
        drift = ArchitectureDrift(
            project_id=project_id,
            drift_type="removed_component",
            severity=DriftSeverity.MEDIUM,
            title=f"{len(removed_keys)} component(s) removed since snapshot",
            description=f"Components removed since '{snap.name}': {', '.join(sorted(list(removed_keys)[:10]))}",
            source_snapshot_id=snapshot_id,
            comparison_target=snap.name,
            metadata_={"removed_keys": sorted(list(removed_keys)[:50])},
        )
        db.add(drift)
        await db.flush()
        await db.refresh(drift)
        drifts.append(drift)

    # Edge count drift
    snap_edge_count = len(snap_data.get("edges", []))
    current_edge_count = len(current_edges)
    edge_diff = abs(current_edge_count - snap_edge_count)
    if edge_diff > max(5, snap_edge_count * 0.2):
        drift = ArchitectureDrift(
            project_id=project_id,
            drift_type="dependency_count_drift",
            severity=DriftSeverity.MEDIUM,
            title=f"Dependency count changed significantly ({snap_edge_count} -> {current_edge_count})",
            description=f"Edge count changed by {edge_diff} since snapshot '{snap.name}'.",
            source_snapshot_id=snapshot_id,
            comparison_target=snap.name,
            metadata_={"old_count": snap_edge_count, "new_count": current_edge_count},
        )
        db.add(drift)
        await db.flush()
        await db.refresh(drift)
        drifts.append(drift)

    return drifts


def _detect_convention_drift(
    nodes: list[ArchitectureNode],
    edges: list[ArchitectureEdge],
    node_map: dict,
) -> list[dict]:
    """Apply convention-based checks to detect architectural drift."""
    drifts: list[dict] = []

    # Check for cross-layer imports
    forbidden_directions = {
        ("model", "api"),  # model should not import from API
        ("model", "service"),  # model should not import from service
        ("service", "api"),  # service should not import from API routes
    }

    for edge in edges:
        from_node = node_map.get(edge.from_node_id)
        to_node = node_map.get(edge.to_node_id)
        if not from_node or not to_node:
            continue

        from_layer = (from_node.metadata_ or {}).get("layer", "other")
        to_layer = (to_node.metadata_ or {}).get("layer", "other")

        if (from_layer, to_layer) in forbidden_directions:
            drifts.append(
                {
                    "drift_type": "cross_layer_import",
                    "severity": DriftSeverity.HIGH,
                    "title": f"Cross-layer import: {from_layer} -> {to_layer}",
                    "description": (
                        f"Module '{from_node.key}' ({from_layer} layer) imports from "
                        f"'{to_node.key}' ({to_layer} layer). This violates layered architecture conventions."
                    ),
                    "metadata_": {
                        "from_node": from_node.key,
                        "to_node": to_node.key,
                        "from_layer": from_layer,
                        "to_layer": to_layer,
                    },
                }
            )

    # Check for undocumented components (inferred but no declared counterpart)
    inferred_only = [n for n in nodes if n.source_type.value == "inferred"]
    declared_keys = {n.key for n in nodes if n.source_type.value == "declared"}
    undocumented = [n for n in inferred_only if n.key not in declared_keys]
    # Only flag if there are declared nodes (meaning someone started documenting)
    if declared_keys and len(undocumented) > len(nodes) * 0.3:
        drifts.append(
            {
                "drift_type": "undocumented_components",
                "severity": DriftSeverity.LOW,
                "title": f"{len(undocumented)} undocumented components",
                "description": (
                    f"{len(undocumented)} out of {len(nodes)} components are inferred but "
                    f"not declared in architecture documentation."
                ),
                "metadata_": {
                    "undocumented_count": len(undocumented),
                    "total_count": len(nodes),
                },
            }
        )

    return drifts


# ── Drift CRUD ───────────────────────────────────────────────────


async def list_drifts(
    db: AsyncSession,
    project_id: uuid.UUID,
    *,
    status: DriftStatus | None = None,
    severity: DriftSeverity | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[ArchitectureDrift], int]:
    query = select(ArchitectureDrift).where(ArchitectureDrift.project_id == project_id)
    if status:
        query = query.where(ArchitectureDrift.status == status)
    if severity:
        query = query.where(ArchitectureDrift.severity == severity)

    total = (
        await db.execute(select(sa_func.count()).select_from(query.subquery()))
    ).scalar_one()
    result = await db.execute(
        query.order_by(ArchitectureDrift.detected_at.desc()).offset(offset).limit(limit)
    )
    return list(result.scalars().all()), total


async def resolve_drift(
    db: AsyncSession, drift_id: uuid.UUID
) -> ArchitectureDrift | None:
    result = await db.execute(
        select(ArchitectureDrift).where(ArchitectureDrift.id == drift_id)
    )
    drift = result.scalar_one_or_none()
    if drift is None:
        return None
    drift.status = DriftStatus.RESOLVED
    drift.resolved_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(drift)
    return drift


async def ignore_drift(
    db: AsyncSession, drift_id: uuid.UUID
) -> ArchitectureDrift | None:
    result = await db.execute(
        select(ArchitectureDrift).where(ArchitectureDrift.id == drift_id)
    )
    drift = result.scalar_one_or_none()
    if drift is None:
        return None
    drift.status = DriftStatus.IGNORED
    drift.resolved_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(drift)
    return drift
