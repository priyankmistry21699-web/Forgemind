"""Repo connection routes — external repository/workspace integration.

FM-049: CRUD, health checks, and sync endpoints for repo connections.
FM-061: Sync metadata refresh / status endpoints.
FM-062: File tree and code content explorer routes.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.repo import (
    RepoConnectionRead,
    RepoConnectionList,
    RepoConnectionCreate,
    RepoConnectionUpdate,
    RepoSyncResult,
    FileTreeResult,
    FileContentResult,
    RepoSyncMetadata,
)
from app.services import repo_service

router = APIRouter()


@router.post(
    "/projects/{project_id}/repos",
    response_model=RepoConnectionRead,
    status_code=201,
)
async def create_connection(
    project_id: uuid.UUID,
    body: RepoConnectionCreate,
    db: AsyncSession = Depends(get_db),
) -> RepoConnectionRead:
    """Create a new repo connection for a project."""
    conn = await repo_service.create_connection(
        db,
        project_id=project_id,
        provider=body.provider,
        repo_url=body.repo_url,
        repo_name=body.repo_name,
        default_branch=body.default_branch,
        credential_env_key=body.credential_env_key,
        config=body.config,
        workspace_path=body.workspace_path,
        base_branch=body.base_branch,
        target_branch=body.target_branch,
        linked_paths=body.linked_paths,
        provider_metadata=body.provider_metadata,
        branch_mode=body.branch_mode,
        target_branch_template=body.target_branch_template,
    )
    await db.commit()
    return RepoConnectionRead.model_validate(conn)


@router.get(
    "/projects/{project_id}/repos",
    response_model=RepoConnectionList,
)
async def list_connections(
    project_id: uuid.UUID,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> RepoConnectionList:
    """List repo connections for a project."""
    connections, total = await repo_service.list_connections(
        db, project_id, limit=limit, offset=offset
    )
    return RepoConnectionList(
        items=[RepoConnectionRead.model_validate(c) for c in connections],
        total=total,
    )


@router.get("/repos/{connection_id}", response_model=RepoConnectionRead)
async def get_connection(
    connection_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> RepoConnectionRead:
    """Get a single repo connection."""
    conn = await repo_service.get_connection(db, connection_id)
    if conn is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repo connection not found",
        )
    return RepoConnectionRead.model_validate(conn)


@router.patch("/repos/{connection_id}", response_model=RepoConnectionRead)
async def update_connection(
    connection_id: uuid.UUID,
    body: RepoConnectionUpdate,
    db: AsyncSession = Depends(get_db),
) -> RepoConnectionRead:
    """Update a repo connection."""
    conn = await repo_service.update_connection(
        db, connection_id,
        **body.model_dump(exclude_unset=True),
    )
    if conn is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repo connection not found",
        )
    await db.commit()
    return RepoConnectionRead.model_validate(conn)


@router.delete("/repos/{connection_id}", status_code=204)
async def delete_connection(
    connection_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Delete a repo connection."""
    deleted = await repo_service.delete_connection(db, connection_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repo connection not found",
        )
    await db.commit()


@router.post("/repos/{connection_id}/health")
async def check_health(
    connection_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Check health of a repo connection."""
    result = await repo_service.check_connection_health(db, connection_id)
    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result["error"],
        )
    await db.commit()
    return result


@router.post("/repos/{connection_id}/sync")
async def sync_connection(
    connection_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Sync a repo connection — verify and update status."""
    result = await repo_service.sync_connection(db, connection_id)
    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result["error"],
        )
    await db.commit()
    return result


# ── FM-061: Sync metadata ───────────────────────────────────────

@router.get("/repos/{connection_id}/sync-status", response_model=RepoSyncMetadata)
async def get_sync_status(
    connection_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> RepoSyncMetadata:
    """Get current sync metadata for a repo connection."""
    result = await repo_service.get_sync_status(db, connection_id)
    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result["error"],
        )
    return RepoSyncMetadata(**result)


@router.post("/repos/{connection_id}/refresh-sync")
async def refresh_sync_metadata(
    connection_id: uuid.UUID,
    commit_sha: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Refresh sync metadata (commit SHA, provider data) for a repo connection."""
    result = await repo_service.refresh_sync_metadata(
        db, connection_id, commit_sha=commit_sha,
    )
    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result["error"],
        )
    await db.commit()
    return result


# ── FM-062: File tree & code content ────────────────────────────

@router.get("/repos/{connection_id}/tree", response_model=FileTreeResult)
async def get_file_tree(
    connection_id: uuid.UUID,
    path: str = Query("", description="Sub-path within workspace"),
    db: AsyncSession = Depends(get_db),
) -> FileTreeResult:
    """Browse the file tree of a linked local workspace."""
    result = await repo_service.get_file_tree(db, connection_id, path)
    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"],
        )
    return FileTreeResult(**result)


@router.get("/repos/{connection_id}/file", response_model=FileContentResult)
async def get_file_content(
    connection_id: uuid.UUID,
    path: str = Query(..., description="File path within workspace"),
    db: AsyncSession = Depends(get_db),
) -> FileContentResult:
    """Fetch file content from a linked local workspace."""
    result = await repo_service.get_file_content(db, connection_id, path)
    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"],
        )
    return FileContentResult(**result)


@router.get("/repos/{connection_id}/file-meta")
async def get_file_metadata(
    connection_id: uuid.UUID,
    path: str = Query(..., description="File path within workspace"),
    db: AsyncSession = Depends(get_db),
):
    """Get metadata for a file without fetching content."""
    result = await repo_service.get_file_metadata(db, connection_id, path)
    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"],
        )
    return result
