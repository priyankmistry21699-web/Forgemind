"""Trust scoring routes — assess and query trust/risk for entities.

FM-050: Trust scoring and risk assessment endpoints.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.trust_score import EntityType, RiskLevel
from app.schemas.trust import TrustScoreRead, TrustScoreList
from app.services import trust_scoring_service

router = APIRouter(prefix="/trust")


@router.post("/tasks/{task_id}/assess", response_model=TrustScoreRead)
async def assess_task(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> TrustScoreRead:
    """Compute and store trust score for a task."""
    try:
        ts = await trust_scoring_service.assess_task(db, task_id)
        await db.commit()
        return TrustScoreRead.model_validate(ts)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )


@router.post("/runs/{run_id}/assess", response_model=TrustScoreRead)
async def assess_run(
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> TrustScoreRead:
    """Compute and store trust score for a run."""
    try:
        ts = await trust_scoring_service.assess_run(db, run_id)
        await db.commit()
        return TrustScoreRead.model_validate(ts)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )


@router.get("/runs/{run_id}/risk-summary")
async def get_run_risk_summary(
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get comprehensive risk summary for a run and all its tasks."""
    try:
        return await trust_scoring_service.get_run_risk_summary(db, run_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )


@router.get("/scores", response_model=TrustScoreList)
async def list_trust_scores(
    project_id: uuid.UUID | None = Query(None),
    run_id: uuid.UUID | None = Query(None),
    risk_level: RiskLevel | None = Query(None),
    entity_type: EntityType | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> TrustScoreList:
    """List trust scores with optional filters."""
    scores = await trust_scoring_service.list_trust_scores(
        db,
        project_id=project_id,
        run_id=run_id,
        risk_level=risk_level,
        entity_type=entity_type,
    )
    return TrustScoreList(
        items=[TrustScoreRead.model_validate(s) for s in scores],
        total=len(scores),
    )


@router.get("/{entity_type}/{entity_id}", response_model=TrustScoreRead)
async def get_trust_score(
    entity_type: EntityType,
    entity_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> TrustScoreRead:
    """Get trust score for a specific entity."""
    ts = await trust_scoring_service.get_trust_score(db, entity_type, entity_id)
    if ts is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trust score not found — run assessment first",
        )
    return TrustScoreRead.model_validate(ts)
