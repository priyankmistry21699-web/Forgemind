"""Routes for execution memory — run summaries, failure analysis, context."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services import run_memory_service

router = APIRouter(prefix="/runs/{run_id}/memory")


@router.get("/summary")
async def get_run_summary(
    run_id: uuid.UUID,
    refresh: bool = False,
    db: AsyncSession = Depends(get_db),
):
    """Return a cached execution summary for the run."""
    summary = await run_memory_service.get_run_summary(
        db, run_id, force_refresh=refresh
    )
    if "error" in summary:
        raise HTTPException(status_code=404, detail=summary["error"])
    return summary


@router.get("/failures")
async def get_failure_analysis(
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Analyse failures and suggest recovery actions."""
    analysis = await run_memory_service.get_failure_analysis(db, run_id)
    if "error" in analysis:
        raise HTTPException(status_code=404, detail=analysis["error"])
    return analysis


@router.get("/context")
async def get_run_context_text(
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Return the assembled text context (same format used by chat service)."""
    summary = await run_memory_service.get_run_summary(db, run_id)
    if "error" in summary:
        raise HTTPException(status_code=404, detail=summary["error"])
    return {"context": run_memory_service.build_context_for_chat(summary)}
