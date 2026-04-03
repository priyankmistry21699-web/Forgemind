"""Architecture graph service - nodes, edges, and snapshots.

FM-081: Core CRUD and graph query operations for the architecture model.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.architecture import (
    ArchitectureNode, ArchitectureEdge, ArchitectureSnapshot,
    NodeType, EdgeType, SourceType, NodeStatus,
)


# ── Nodes ────────────────────────────────────────────────────────

async def create_node(
    db: AsyncSession,
    *,
    project_id: uuid.UUID,
    node_type: NodeType,
    key: str,
    name: str,
    workspace_id: uuid.UUID | None = None,
    repo_id: uuid.UUID | None = None,
    path: str | None = None,
    language: str | None = None,
    metadata_: dict | None = None,
    source_type: SourceType = SourceType.INFERRED,
    status: NodeStatus = NodeStatus.ACTIVE,
) -> ArchitectureNode:
    node = ArchitectureNode(
        project_id=project_id,
        workspace_id=workspace_id,
        repo_id=repo_id,
        node_type=node_type,
        key=key,
        name=name,
        path=path,
        language=language,
        metadata_=metadata_,
        source_type=source_type,
        status=status,
    )
    db.add(node)
    await db.flush()
    await db.refresh(node)
    return node


async def get_node(
    db: AsyncSession, node_id: uuid.UUID
) -> ArchitectureNode | None:
    result = await db.execute(
        select(ArchitectureNode).where(ArchitectureNode.id == node_id)
    )
    return result.scalar_one_or_none()


async def list_nodes(
    db: AsyncSession,
    project_id: uuid.UUID,
    *,
    node_type: NodeType | None = None,
    status: NodeStatus | None = None,
    limit: int = 200,
    offset: int = 0,
) -> tuple[list[ArchitectureNode], int]:
    query = select(ArchitectureNode).where(
        ArchitectureNode.project_id == project_id
    )
    if node_type:
        query = query.where(ArchitectureNode.node_type == node_type)
    if status:
        query = query.where(ArchitectureNode.status == status)

    total = (await db.execute(
        select(sa_func.count()).select_from(query.subquery())
    )).scalar_one()
    result = await db.execute(
        query.order_by(ArchitectureNode.created_at.desc()).offset(offset).limit(limit)
    )
    return list(result.scalars().all()), total


async def update_node(
    db: AsyncSession,
    node_id: uuid.UUID,
    **kwargs,
) -> ArchitectureNode | None:
    node = await get_node(db, node_id)
    if node is None:
        return None
    for k, v in kwargs.items():
        if v is not None:
            setattr(node, k, v)
    await db.flush()
    await db.refresh(node)
    return node


async def delete_node(
    db: AsyncSession, node_id: uuid.UUID
) -> bool:
    node = await get_node(db, node_id)
    if node is None:
        return False
    await db.delete(node)
    await db.flush()
    return True


# ── Edges ────────────────────────────────────────────────────────

async def create_edge(
    db: AsyncSession,
    *,
    project_id: uuid.UUID,
    from_node_id: uuid.UUID,
    to_node_id: uuid.UUID,
    edge_type: EdgeType,
    workspace_id: uuid.UUID | None = None,
    confidence_score: float = 1.0,
    metadata_: dict | None = None,
    source_type: SourceType = SourceType.INFERRED,
) -> ArchitectureEdge:
    edge = ArchitectureEdge(
        project_id=project_id,
        workspace_id=workspace_id,
        from_node_id=from_node_id,
        to_node_id=to_node_id,
        edge_type=edge_type,
        confidence_score=confidence_score,
        metadata_=metadata_,
        source_type=source_type,
    )
    db.add(edge)
    await db.flush()
    await db.refresh(edge)
    return edge


async def list_edges(
    db: AsyncSession,
    project_id: uuid.UUID,
    *,
    edge_type: EdgeType | None = None,
    limit: int = 500,
    offset: int = 0,
) -> tuple[list[ArchitectureEdge], int]:
    query = select(ArchitectureEdge).where(
        ArchitectureEdge.project_id == project_id
    )
    if edge_type:
        query = query.where(ArchitectureEdge.edge_type == edge_type)

    total = (await db.execute(
        select(sa_func.count()).select_from(query.subquery())
    )).scalar_one()
    result = await db.execute(
        query.order_by(ArchitectureEdge.created_at.desc()).offset(offset).limit(limit)
    )
    return list(result.scalars().all()), total


async def delete_edge(
    db: AsyncSession, edge_id: uuid.UUID
) -> bool:
    result = await db.execute(
        select(ArchitectureEdge).where(ArchitectureEdge.id == edge_id)
    )
    edge = result.scalar_one_or_none()
    if edge is None:
        return False
    await db.delete(edge)
    await db.flush()
    return True


async def get_neighbors(
    db: AsyncSession, node_id: uuid.UUID
) -> tuple[list[ArchitectureEdge], list[ArchitectureEdge]]:
    """Return (incoming, outgoing) edges for a node."""
    incoming_result = await db.execute(
        select(ArchitectureEdge).where(ArchitectureEdge.to_node_id == node_id)
    )
    outgoing_result = await db.execute(
        select(ArchitectureEdge).where(ArchitectureEdge.from_node_id == node_id)
    )
    return list(incoming_result.scalars().all()), list(outgoing_result.scalars().all())


# ── Graph queries ────────────────────────────────────────────────

async def get_full_graph(
    db: AsyncSession, project_id: uuid.UUID
) -> tuple[list[ArchitectureNode], list[ArchitectureEdge]]:
    """Get all nodes and edges for a project."""
    nodes_result = await db.execute(
        select(ArchitectureNode).where(
            ArchitectureNode.project_id == project_id,
            ArchitectureNode.status == NodeStatus.ACTIVE,
        )
    )
    edges_result = await db.execute(
        select(ArchitectureEdge).where(
            ArchitectureEdge.project_id == project_id
        )
    )
    return list(nodes_result.scalars().all()), list(edges_result.scalars().all())


# ── Snapshots ────────────────────────────────────────────────────

async def create_snapshot(
    db: AsyncSession,
    *,
    project_id: uuid.UUID,
    name: str,
    workspace_id: uuid.UUID | None = None,
    source: str | None = None,
) -> ArchitectureSnapshot:
    """Capture current graph state as a snapshot."""
    nodes, edges = await get_full_graph(db, project_id)

    snapshot_data = {
        "nodes": [
            {
                "id": str(n.id),
                "node_type": n.node_type.value,
                "key": n.key,
                "name": n.name,
                "path": n.path,
                "language": n.language,
            }
            for n in nodes
        ],
        "edges": [
            {
                "id": str(e.id),
                "from_node_id": str(e.from_node_id),
                "to_node_id": str(e.to_node_id),
                "edge_type": e.edge_type.value,
                "confidence_score": e.confidence_score,
            }
            for e in edges
        ],
    }

    summary = {
        "node_count": len(nodes),
        "edge_count": len(edges),
        "node_types": list(set(n.node_type.value for n in nodes)),
        "edge_types": list(set(e.edge_type.value for e in edges)),
    }

    snap = ArchitectureSnapshot(
        project_id=project_id,
        workspace_id=workspace_id,
        name=name,
        source=source,
        summary=summary,
        node_count=len(nodes),
        edge_count=len(edges),
        snapshot_data=snapshot_data,
    )
    db.add(snap)
    await db.flush()
    await db.refresh(snap)
    return snap


async def get_snapshot(
    db: AsyncSession, snapshot_id: uuid.UUID
) -> ArchitectureSnapshot | None:
    result = await db.execute(
        select(ArchitectureSnapshot).where(ArchitectureSnapshot.id == snapshot_id)
    )
    return result.scalar_one_or_none()


async def list_snapshots(
    db: AsyncSession,
    project_id: uuid.UUID,
    *,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[ArchitectureSnapshot], int]:
    query = select(ArchitectureSnapshot).where(
        ArchitectureSnapshot.project_id == project_id
    )
    total = (await db.execute(
        select(sa_func.count()).select_from(query.subquery())
    )).scalar_one()
    result = await db.execute(
        query.order_by(ArchitectureSnapshot.generated_at.desc()).offset(offset).limit(limit)
    )
    return list(result.scalars().all()), total
