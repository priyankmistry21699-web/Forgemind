"""Repo connection routes — external repository/workspace integration.

FM-049: CRUD, health checks, and sync endpoints for repo connections.
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
