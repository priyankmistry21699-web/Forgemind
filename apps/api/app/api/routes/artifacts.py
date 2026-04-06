import uuid

from fastapi import APIRouter, Depends, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user_id
from app.db.session import get_db
from app.schemas.artifact import (
    ArtifactCreate,
    ArtifactRead,
    ArtifactList,
    ArtifactUpdate,
)
from app.services import artifact_service, plan_artifact_service

router = APIRouter()


@router.post(
    "/projects/{project_id}/artifacts",
    response_model=ArtifactRead,
    status_code=201,
)
async def create_artifact(
    project_id: uuid.UUID,
    data: ArtifactCreate,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> ArtifactRead:
    """Create a new artifact linked to a project (and optionally a run/task)."""
    artifact = await artifact_service.create_artifact(db, project_id, data)
    await db.commit()
    return ArtifactRead.model_validate(artifact)


@router.get(
    "/projects/{project_id}/artifacts",
    response_model=ArtifactList,
)
async def list_artifacts(
    project_id: uuid.UUID,
    run_id: uuid.UUID | None = Query(None),
    task_id: uuid.UUID | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> ArtifactList:
    """List artifacts for a project, optionally filtered by run or task."""
    artifacts, total = await artifact_service.list_artifacts_by_project(
        db, project_id, run_id=run_id, task_id=task_id, limit=limit, offset=offset
    )
    return ArtifactList(
        items=[ArtifactRead.model_validate(a) for a in artifacts],
        total=total,
    )


@router.get("/artifacts/{artifact_id}", response_model=ArtifactRead)
async def get_artifact(
    artifact_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> ArtifactRead:
    """Get a single artifact by ID."""
    artifact = await artifact_service.get_artifact(db, artifact_id)
    return ArtifactRead.model_validate(artifact)


@router.patch("/artifacts/{artifact_id}", response_model=ArtifactRead)
async def update_artifact(
    artifact_id: uuid.UUID,
    data: ArtifactUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> ArtifactRead:
    """Update an artifact's title, content, or metadata. Bumps version on content changes."""
    artifact = await artifact_service.update_artifact(db, artifact_id, data)
    await db.commit()
    return ArtifactRead.model_validate(artifact)


@router.delete("/artifacts/{artifact_id}", status_code=204)
async def delete_artifact(
    artifact_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> None:
    """Delete an artifact."""
    await artifact_service.delete_artifact(db, artifact_id)
    await db.commit()


# FM-106: PLAN export endpoint
@router.get("/runs/{run_id}/plan/export")
async def export_plan(
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Export the PLAN (with linked SPEC) as markdown or JSON metadata."""
    data = await plan_artifact_service.get_plan_export_data(db, run_id)
    return data


@router.get("/runs/{run_id}/plan/export/markdown")
async def export_plan_markdown(
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Download the PLAN as a markdown file."""
    md = await plan_artifact_service.export_plan_markdown(db, run_id)
    if md is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="No PLAN artifact found")
    return PlainTextResponse(
        content=md,
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="plan-{run_id}.md"'},
    )
