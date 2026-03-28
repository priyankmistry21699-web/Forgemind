"""Repo connection service — external repository/workspace management.

FM-049: Provides:
- Repository connection CRUD
- Connection status management
- Sync/health check operations
- Workspace path validation
FM-061: Extended with sync metadata refresh.
FM-062: File tree and code context explorer.
FM-066: Branch strategy management.
"""

import os
import uuid
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.repo_connection import (
    RepoConnection,
    RepoProvider,
    RepoConnectionStatus,
    SyncStatus,
    BranchMode,
)

logger = logging.getLogger(__name__)

# FM-062: File size guard (1 MB max for file content fetch)
MAX_FILE_SIZE_BYTES = 1_048_576
# FM-062: Max entries in file tree listing
MAX_TREE_ENTRIES = 500

# FM-062: Common language extension map
_LANG_MAP: dict[str, str] = {
    ".py": "python", ".js": "javascript", ".ts": "typescript",
    ".tsx": "typescript", ".jsx": "javascript", ".java": "java",
    ".go": "go", ".rs": "rust", ".rb": "ruby", ".cpp": "cpp",
    ".c": "c", ".cs": "csharp", ".php": "php", ".swift": "swift",
    ".kt": "kotlin", ".sql": "sql", ".sh": "shell", ".yml": "yaml",
    ".yaml": "yaml", ".json": "json", ".md": "markdown", ".html": "html",
    ".css": "css", ".scss": "scss",
}


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
    base_branch: str | None = None,
    target_branch: str | None = None,
    linked_paths: list | None = None,
    provider_metadata: dict | None = None,
    branch_mode: BranchMode | None = None,
    target_branch_template: str | None = None,
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
        base_branch=base_branch,
        target_branch=target_branch,
        linked_paths=linked_paths,
        provider_metadata=provider_metadata,
        branch_mode=branch_mode,
        target_branch_template=target_branch_template,
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
        # FM-061
        "base_branch", "target_branch", "linked_paths",
        "provider_metadata",
        # FM-066
        "branch_mode", "target_branch_template",
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
    """Check health of a repo connection."""
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
    """Sync a repo connection — verify and update status."""
    health = await check_connection_health(db, connection_id)
    if "error" in health:
        return health

    conn = await get_connection(db, connection_id)
    if conn and health.get("healthy"):
        conn.status = RepoConnectionStatus.CONNECTED
        conn.last_sync_status = SyncStatus.SUCCESS
        conn.last_sync_error = None
        conn.last_synced_at = datetime.now(timezone.utc)
        await db.flush()
    elif conn:
        conn.last_sync_status = SyncStatus.FAILED
        conn.last_sync_error = ", ".join(health.get("issues", []))
        await db.flush()

    return {
        "repo_id": str(connection_id),
        "status": "synced" if health.get("healthy") else "error",
        "message": "Repository synced successfully" if health.get("healthy")
                   else f"Sync failed: {', '.join(health.get('issues', []))}",
        "synced_at": conn.last_synced_at.isoformat() if conn and conn.last_synced_at else None,
    }


# ── FM-061: Sync metadata refresh ──────────────────────────────

async def refresh_sync_metadata(
    db: AsyncSession,
    connection_id: uuid.UUID,
    *,
    commit_sha: str | None = None,
    provider_metadata: dict | None = None,
) -> dict[str, Any]:
    """Refresh sync metadata for a repo connection."""
    conn = await get_connection(db, connection_id)
    if conn is None:
        return {"error": "Connection not found"}

    conn.last_sync_status = SyncStatus.SUCCESS
    conn.last_sync_error = None
    conn.last_synced_at = datetime.now(timezone.utc)
    if commit_sha:
        conn.last_synced_commit = commit_sha
    if provider_metadata:
        conn.provider_metadata = provider_metadata
    await db.flush()

    return {
        "connection_id": str(connection_id),
        "last_sync_status": conn.last_sync_status.value if conn.last_sync_status else None,
        "last_synced_commit": conn.last_synced_commit,
        "last_synced_at": conn.last_synced_at.isoformat() if conn.last_synced_at else None,
    }


async def get_sync_status(
    db: AsyncSession,
    connection_id: uuid.UUID,
) -> dict[str, Any]:
    """Return sync status summary for a repo connection."""
    conn = await get_connection(db, connection_id)
    if conn is None:
        return {"error": "Connection not found"}

    return {
        "connection_id": str(connection_id),
        "last_sync_status": conn.last_sync_status.value if conn.last_sync_status else None,
        "last_sync_error": conn.last_sync_error,
        "last_synced_commit": conn.last_synced_commit,
        "last_synced_at": conn.last_synced_at.isoformat() if conn.last_synced_at else None,
    }


# ── FM-062: File tree and code context ──────────────────────────

def _detect_language(file_path: str) -> str | None:
    ext = Path(file_path).suffix.lower()
    return _LANG_MAP.get(ext)


async def get_file_tree(
    db: AsyncSession,
    connection_id: uuid.UUID,
    path: str = "",
) -> dict[str, Any]:
    """Browse the file tree of a linked repo/workspace (local provider only)."""
    conn = await get_connection(db, connection_id)
    if conn is None:
        return {"error": "Connection not found"}

    if conn.provider != RepoProvider.LOCAL or not conn.workspace_path:
        return {"error": "File tree browsing requires a local workspace connection"}

    base = Path(conn.workspace_path).resolve()
    target = (base / path).resolve()

    # Path traversal guard
    if not str(target).startswith(str(base)):
        return {"error": "Path traversal not allowed"}

    if not target.is_dir():
        return {"error": f"Not a directory: {path}"}

    entries: list[dict[str, Any]] = []
    try:
        for item in sorted(target.iterdir()):
            if item.name.startswith("."):
                continue  # skip hidden files
            if len(entries) >= MAX_TREE_ENTRIES:
                break
            resolved_item = item.resolve()
            entry = {
                "name": item.name,
                "path": str(resolved_item.relative_to(base)),
                "is_directory": item.is_dir(),
                "size": item.stat().st_size if item.is_file() else None,
            }
            entries.append(entry)
    except PermissionError:
        return {"error": f"Permission denied: {path}"}

    return {
        "connection_id": str(connection_id),
        "base_path": path or ".",
        "entries": entries,
    }


async def get_file_content(
    db: AsyncSession,
    connection_id: uuid.UUID,
    path: str,
) -> dict[str, Any]:
    """Fetch file content from a linked local workspace."""
    conn = await get_connection(db, connection_id)
    if conn is None:
        return {"error": "Connection not found"}

    if conn.provider != RepoProvider.LOCAL or not conn.workspace_path:
        return {"error": "File content retrieval requires a local workspace connection"}

    base = Path(conn.workspace_path).resolve()
    target = (base / path).resolve()

    # Path traversal guard
    if not str(target).startswith(str(base)):
        return {"error": "Path traversal not allowed"}

    if not target.is_file():
        return {"error": f"Not a file: {path}"}

    file_size = target.stat().st_size
    if file_size > MAX_FILE_SIZE_BYTES:
        return {"error": f"File too large ({file_size} bytes, max {MAX_FILE_SIZE_BYTES})"}

    try:
        content = target.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return {"error": f"Cannot read file: {e}"}

    return {
        "connection_id": str(connection_id),
        "path": path,
        "content": content,
        "size": file_size,
        "language": _detect_language(path),
    }


async def get_file_metadata(
    db: AsyncSession,
    connection_id: uuid.UUID,
    path: str,
) -> dict[str, Any]:
    """Get metadata for a file without fetching full content."""
    conn = await get_connection(db, connection_id)
    if conn is None:
        return {"error": "Connection not found"}

    if conn.provider != RepoProvider.LOCAL or not conn.workspace_path:
        return {"error": "File metadata requires a local workspace connection"}

    base = Path(conn.workspace_path).resolve()
    target = (base / path).resolve()

    if not str(target).startswith(str(base)):
        return {"error": "Path traversal not allowed"}

    if not target.exists():
        return {"error": f"Path not found: {path}"}

    stat = target.stat()
    return {
        "connection_id": str(connection_id),
        "path": path,
        "name": target.name,
        "is_directory": target.is_dir(),
        "size": stat.st_size,
        "language": _detect_language(path) if target.is_file() else None,
        "modified_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
    }


def build_context_snippet(
    workspace_path: str,
    file_paths: list[str],
    *,
    max_lines_per_file: int = 100,
) -> str:
    """Build a context snippet from selected files for planning/execution."""
    base = Path(workspace_path).resolve()
    parts: list[str] = []

    for fp in file_paths:
        target = (base / fp).resolve()
        if not str(target).startswith(str(base)):
            continue
        if not target.is_file():
            continue
        if target.stat().st_size > MAX_FILE_SIZE_BYTES:
            parts.append(f"--- {fp} (skipped: too large) ---")
            continue

        try:
            lines = target.read_text(encoding="utf-8", errors="replace").splitlines()
            truncated = lines[:max_lines_per_file]
            parts.append(f"--- {fp} ---")
            parts.append("\n".join(truncated))
            if len(lines) > max_lines_per_file:
                parts.append(f"... ({len(lines) - max_lines_per_file} more lines)")
        except Exception:
            parts.append(f"--- {fp} (read error) ---")

    return "\n\n".join(parts)
