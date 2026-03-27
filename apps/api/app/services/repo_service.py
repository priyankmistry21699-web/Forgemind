"""Repo connection service — external repository/workspace management.

FM-049: Provides:
- Repository connection CRUD
- Connection status management
- Sync/health check operations
- Workspace path validation
"""

import os
import uuid
import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.repo_connection import (
    RepoConnection,
    RepoProvider,
    RepoConnectionStatus,
)

logger = logging.getLogger(__name__)


async def create_connection(
    db: AsyncSession,
    *,
    project_id: uuid.UUID,
    provider: RepoProvider,
    repo_url: str,
    repo_name: str,
    default_branch: str = "main",
    credential_env_key: str | None = None,
    config: dict | None = None,
    workspace_path: str | None = None,
) -> RepoConnection:
    """Create a new repository connection."""
    conn = RepoConnection(
        project_id=project_id,
        provider=provider,
        repo_url=repo_url,
        repo_name=repo_name,
        default_branch=default_branch,
        credential_env_key=credential_env_key,
        config=config,
        workspace_path=workspace_path,
        status=RepoConnectionStatus.PENDING,
    )
    db.add(conn)
    await db.flush()
    return conn


async def get_connection(
    db: AsyncSession,
    connection_id: uuid.UUID,
) -> RepoConnection | None:
    """Get a single repo connection by ID."""
    result = await db.execute(
        select(RepoConnection).where(RepoConnection.id == connection_id)
    )
    return result.scalar_one_or_none()


async def list_connections(
    db: AsyncSession,
    project_id: uuid.UUID,
    *,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[RepoConnection], int]:
    """List repo connections for a project."""
    query = select(RepoConnection).where(
        RepoConnection.project_id == project_id
    )

    count_result = await db.execute(
        select(sa_func.count()).select_from(query.subquery())
    )
    total = count_result.scalar_one()

    result = await db.execute(
        query.order_by(RepoConnection.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    return list(result.scalars().all()), total


async def update_connection(
    db: AsyncSession,
    connection_id: uuid.UUID,
    **updates: Any,
) -> RepoConnection | None:
    """Update a repo connection."""
    conn = await get_connection(db, connection_id)
    if conn is None:
        return None

    allowed_fields = {
        "default_branch", "credential_env_key", "config",
        "workspace_path", "status",
    }
    for key, value in updates.items():
        if key in allowed_fields and value is not None:
            setattr(conn, key, value)

    await db.flush()
    return conn


async def delete_connection(
    db: AsyncSession,
    connection_id: uuid.UUID,
) -> bool:
    """Delete a repo connection."""
    conn = await get_connection(db, connection_id)
    if conn is None:
        return False
    await db.delete(conn)
    await db.flush()
    return True


async def check_connection_health(
    db: AsyncSession,
    connection_id: uuid.UUID,
) -> dict[str, Any]:
    """Check community health of a repo connection.

    For local repos, checks workspace path existence.
    For remote repos, checks if credential env var is set.
    """
    conn = await get_connection(db, connection_id)
    if conn is None:
        return {"error": "Connection not found"}

    issues: list[str] = []
    healthy = True

    if conn.provider == RepoProvider.LOCAL:
        if conn.workspace_path and not os.path.isdir(conn.workspace_path):
            issues.append(f"Workspace path does not exist: {conn.workspace_path}")
            healthy = False
    else:
        # Remote repo — check credential
        if conn.credential_env_key:
            if not os.environ.get(conn.credential_env_key, "").strip():
                issues.append(f"Credential env var '{conn.credential_env_key}' is not set")
                healthy = False
        else:
            issues.append("No credential configured")
            healthy = False

    new_status = RepoConnectionStatus.CONNECTED if healthy else RepoConnectionStatus.ERROR
    conn.status = new_status
    if healthy:
        conn.last_synced_at = datetime.now(timezone.utc)
    await db.flush()

    return {
        "connection_id": str(connection_id),
        "repo_name": conn.repo_name,
        "provider": conn.provider.value,
        "healthy": healthy,
        "status": new_status.value,
        "issues": issues,
    }


async def sync_connection(
    db: AsyncSession,
    connection_id: uuid.UUID,
) -> dict[str, Any]:
    """Sync a repo connection — verify and update status.

    In a full implementation, this would clone/pull the repo.
    Currently performs a health check and marks as synced.
    """
    health = await check_connection_health(db, connection_id)
    if "error" in health:
        return health

    conn = await get_connection(db, connection_id)
    if conn and health.get("healthy"):
        conn.status = RepoConnectionStatus.CONNECTED
        conn.last_synced_at = datetime.now(timezone.utc)
        await db.flush()

    return {
        "repo_id": str(connection_id),
        "status": "synced" if health.get("healthy") else "error",
        "message": "Repository synced successfully" if health.get("healthy")
                   else f"Sync failed: {', '.join(health.get('issues', []))}",
        "synced_at": conn.last_synced_at.isoformat() if conn and conn.last_synced_at else None,
    }
