"""FM-124/125/126/127/128: Delivery, Review, Traceability, Memory, Confidence routes.

Run-scoped delivery and analysis endpoints.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.auth import get_current_user_id
from app.services.authz_service import check_project_permission, Action
from app.services import delivery_artifact_service, traceability_service
from app.services import run_memory_enrichment_service, release_confidence_service
from app.models.run import Run
from sqlalchemy import select

router = APIRouter(prefix="/runs/{run_id}")


async def _resolve_project_for_run(
    db: AsyncSession,
    run_id: uuid.UUID,
) -> uuid.UUID:
    """Resolve project_id from run."""
    result = await db.execute(select(Run.project_id).where(Run.id == run_id))
    row = result.first()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found",
        )
    return row[0]


# ---------------------------------------------------------------------------
# FM-124: Delivery artifacts
# ---------------------------------------------------------------------------


@router.post("/delivery-artifacts", status_code=status.HTTP_201_CREATED)
async def generate_delivery_artifact(
    run_id: uuid.UUID,
    kind: str = Query(
        default="implementation_summary",
        description="Delivery artifact kind: implementation_summary, changelog_draft, release_note_draft, completion_bundle",
    ),
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> dict:
    """Generate a delivery artifact for a run."""
    pid = await _resolve_project_for_run(db, run_id)
    await check_project_permission(db, pid, user_id, Action.PROJECT_UPDATE)

    try:
        artifact = await delivery_artifact_service.generate_delivery_artifact(
            db, run_id=run_id, project_id=pid, artifact_kind=kind
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    await db.commit()
    return {
        "id": str(artifact.id),
        "title": artifact.title,
        "artifact_type": artifact.artifact_type.value,
        "delivery_kind": kind,
    }


# ---------------------------------------------------------------------------
# FM-125: Review packages
# ---------------------------------------------------------------------------


@router.post("/review-package", status_code=status.HTTP_201_CREATED)
async def generate_review_package(
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> dict:
    """Generate a comprehensive review package for a run."""
    pid = await _resolve_project_for_run(db, run_id)
    await check_project_permission(db, pid, user_id, Action.PROJECT_UPDATE)

    try:
        artifact = await delivery_artifact_service.generate_review_package(
            db, run_id=run_id, project_id=pid
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    await db.commit()
    return {
        "id": str(artifact.id),
        "title": artifact.title,
        "artifact_type": artifact.artifact_type.value,
    }


# ---------------------------------------------------------------------------
# FM-126: Traceability
# ---------------------------------------------------------------------------


@router.get("/traceability")
async def get_traceability(
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> dict:
    """Get end-to-end traceability graph for a run."""
    pid = await _resolve_project_for_run(db, run_id)
    await check_project_permission(db, pid, user_id, Action.PROJECT_VIEW)

    result = await traceability_service.compute_traceability(db, run_id)
    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=result["error"]
        )
    return result


# ---------------------------------------------------------------------------
# FM-127: Run memory enrichment
# ---------------------------------------------------------------------------


@router.get("/memory")
async def get_run_memory(
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> dict:
    """Get structured run memory enrichment."""
    pid = await _resolve_project_for_run(db, run_id)
    await check_project_permission(db, pid, user_id, Action.PROJECT_VIEW)

    result = await run_memory_enrichment_service.enrich_run_memory(db, run_id)
    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=result["error"]
        )
    return result


# ---------------------------------------------------------------------------
# FM-128: Release confidence scoring
# ---------------------------------------------------------------------------


@router.get("/confidence")
async def get_release_confidence(
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> dict:
    """Get explainable release confidence score for a run."""
    pid = await _resolve_project_for_run(db, run_id)
    await check_project_permission(db, pid, user_id, Action.PROJECT_VIEW)

    result = await release_confidence_service.compute_release_confidence(db, run_id)
    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=result["error"]
        )
    return result
