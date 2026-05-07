"""FM-233–240: Platform intelligence API endpoints.

GET  /agents/{slug}/performance          — FM-233 agent perf snapshots
GET  /projects/{id}/prompt-versions      — FM-234 prompt versions
POST /projects/{id}/prompt-versions      — FM-234 create version
POST /projects/{id}/prompt-versions/{vid}/rollback — FM-234 rollback
GET  /projects/{id}/cost-forecast        — FM-236 budget forecast
GET  /runs/{id}/cost-attribution         — FM-237 cost attribution
POST /approvals/bulk-decide              — FM-238 bulk approve/reject
POST /runs/bulk-archive                  — FM-238 bulk archive
GET  /projects/{id}/slos                 — FM-239 SLO summary
POST /projects/{id}/slos                 — FM-239 create SLO
POST /projects/{id}/slos/{sid}/compute   — FM-239 compute attainment
GET  /projects/{id}/anomalies            — FM-240 list anomalies
POST /projects/{id}/anomalies/scan       — FM-240 trigger scan
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user_id
from app.db.session import get_db
from app.models.platform_intelligence import SLOMetric

router = APIRouter()


# ---------------------------------------------------------------------------
# FM-233: Agent performance
# ---------------------------------------------------------------------------


@router.get("/agents/{agent_slug}/performance")
async def get_agent_performance(
    agent_slug: str,
    project_id: uuid.UUID | None = Query(None),
    days: int = Query(30, le=90),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user_id),
) -> dict:
    from app.services.agent_performance_service import get_agent_performance

    data = await get_agent_performance(db, agent_slug, project_id=project_id, days=days)
    return {"agent_slug": agent_slug, "snapshots": data}


# ---------------------------------------------------------------------------
# FM-234: Prompt versions
# ---------------------------------------------------------------------------


class PromptVersionIn(BaseModel):
    role: str
    content: str
    change_summary: str | None = None


@router.get("/projects/{project_id}/prompt-versions")
async def list_prompt_versions(
    project_id: uuid.UUID,
    role: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user_id),
) -> dict:
    from app.services.prompt_version_service import list_versions

    versions = await list_versions(db, project_id, role=role)
    return {
        "items": [
            {
                "id": str(v.id),
                "role": v.role,
                "version": v.version,
                "is_active": v.is_active,
                "change_summary": v.change_summary,
                "created_by": v.created_by,
                "created_at": v.created_at.isoformat(),
            }
            for v in versions
        ],
        "total": len(versions),
    }


@router.post("/projects/{project_id}/prompt-versions", status_code=201)
async def create_prompt_version(
    project_id: uuid.UUID,
    body: PromptVersionIn,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
) -> dict:
    from app.services.prompt_version_service import create_version

    pv = await create_version(
        db,
        project_id=project_id,
        role=body.role,
        content=body.content,
        change_summary=body.change_summary,
        created_by=str(user_id),
    )
    await db.commit()
    return {"id": str(pv.id), "role": pv.role, "version": pv.version}


@router.post("/projects/{project_id}/prompt-versions/{version_id}/rollback")
async def rollback_prompt_version(
    project_id: uuid.UUID,
    version_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user_id),
) -> dict:
    from app.services.prompt_version_service import rollback_to_version

    pv = await rollback_to_version(db, version_id)
    if pv is None:
        raise HTTPException(status_code=404, detail="Version not found")
    await db.commit()
    return {"id": str(pv.id), "role": pv.role, "version": pv.version, "is_active": True}


# ---------------------------------------------------------------------------
# FM-236: Budget forecasting
# ---------------------------------------------------------------------------


@router.get("/projects/{project_id}/cost-forecast")
async def get_cost_forecast(
    project_id: uuid.UUID,
    budget_usd: float | None = Query(None),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user_id),
) -> dict:
    from app.services.cost_forecast_service import generate_forecast

    forecast = await generate_forecast(db, project_id, budget_usd=budget_usd)
    await db.commit()
    return {
        "project_id": str(project_id),
        "forecast_month": forecast.forecast_month,
        "actual_spend_usd": forecast.actual_spend_usd,
        "forecasted_spend_usd": forecast.forecasted_spend_usd,
        "budget_usd": forecast.budget_usd,
        "burn_rate_usd_per_day": forecast.burn_rate_usd_per_day,
        "days_remaining": forecast.days_remaining,
        "will_exceed_budget": forecast.will_exceed_budget,
        "confidence": forecast.confidence,
        "breakdown_by_agent": forecast.breakdown_by_agent,
    }


# ---------------------------------------------------------------------------
# FM-237: Cost attribution
# ---------------------------------------------------------------------------


@router.get("/runs/{run_id}/cost-attribution")
async def get_cost_attribution(
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user_id),
) -> dict:
    from app.services.cost_forecast_service import get_run_cost_attribution

    return await get_run_cost_attribution(db, run_id)


# ---------------------------------------------------------------------------
# FM-238: Bulk operations
# ---------------------------------------------------------------------------


class BulkDecideIn(BaseModel):
    approval_ids: list[uuid.UUID]
    decision: str  # "approved" | "rejected"
    comment: str | None = None


class BulkArchiveRunsIn(BaseModel):
    run_ids: list[uuid.UUID]


@router.post("/approvals/bulk-decide")
async def bulk_decide_approvals(
    body: BulkDecideIn,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
) -> dict:
    from app.models.approval_request import ApprovalRequest, ApprovalStatus
    from datetime import datetime, timezone

    if body.decision not in ("approved", "rejected"):
        raise HTTPException(status_code=422, detail="decision must be 'approved' or 'rejected'")

    new_status = ApprovalStatus.APPROVED if body.decision == "approved" else ApprovalStatus.REJECTED
    updated = 0
    now = datetime.now(timezone.utc)

    for aid in body.approval_ids[:100]:
        approval = await db.get(ApprovalRequest, aid)
        if approval and approval.status == ApprovalStatus.PENDING:
            approval.status = new_status
            approval.decided_by = str(user_id)
            approval.decision_comment = body.comment
            approval.decided_at = now
            updated += 1

    await db.commit()
    return {"updated": updated, "decision": body.decision}


@router.post("/runs/bulk-archive")
async def bulk_archive_runs(
    body: BulkArchiveRunsIn,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user_id),
) -> dict:
    from app.models.run import Run, RunStatus
    from datetime import datetime, timezone

    archived = 0
    now = datetime.now(timezone.utc)

    for rid in body.run_ids[:100]:
        run = await db.get(Run, rid)
        if run and run.archived_at is None:
            run.archived_at = now
            archived += 1

    await db.commit()
    return {"archived": archived}


# ---------------------------------------------------------------------------
# FM-239: SLO tracking
# ---------------------------------------------------------------------------


class SLOIn(BaseModel):
    name: str
    metric: SLOMetric
    threshold: float
    target_pct: float = 0.99
    window_days: int = 30


@router.get("/projects/{project_id}/slos")
async def list_slos(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user_id),
) -> dict:
    from app.services.slo_service import get_slo_summary

    summary = await get_slo_summary(db, project_id)
    return {"items": summary, "total": len(summary)}


@router.post("/projects/{project_id}/slos", status_code=201)
async def create_slo(
    project_id: uuid.UUID,
    body: SLOIn,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user_id),
) -> dict:
    from app.services.slo_service import create_slo as _create_slo

    slo = await _create_slo(
        db,
        project_id=project_id,
        name=body.name,
        metric=body.metric,
        threshold=body.threshold,
        target_pct=body.target_pct,
        window_days=body.window_days,
    )
    await db.commit()
    return {"id": str(slo.id), "name": slo.name, "metric": slo.metric.value}


@router.post("/projects/{project_id}/slos/{slo_id}/compute")
async def compute_slo(
    project_id: uuid.UUID,
    slo_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user_id),
) -> dict:
    from app.models.platform_intelligence import SLOTarget
    from app.services.slo_service import compute_slo_attainment

    slo = await db.get(SLOTarget, slo_id)
    if slo is None or slo.project_id != project_id:
        raise HTTPException(status_code=404, detail="SLO not found")

    result = await compute_slo_attainment(db, slo)
    await db.commit()
    return {
        "slo_id": str(slo_id),
        "attainment_pct": result.attainment_pct,
        "met": result.met,
        "total_events": result.total_events,
        "p50": result.p50,
        "p95": result.p95,
        "p99": result.p99,
    }


# ---------------------------------------------------------------------------
# FM-240: Anomaly detection
# ---------------------------------------------------------------------------


@router.get("/projects/{project_id}/anomalies")
async def list_anomalies(
    project_id: uuid.UUID,
    resolved: bool | None = Query(None),
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user_id),
) -> dict:
    from app.services.anomaly_service import list_anomalies as _list

    anomalies = await _list(db, project_id, resolved=resolved, limit=limit)
    return {
        "items": [
            {
                "id": str(a.id),
                "type": a.anomaly_type.value,
                "severity": a.severity.value,
                "title": a.title,
                "metric_value": a.metric_value,
                "deviation_pct": a.deviation_pct,
                "resolved": a.resolved,
                "detected_at": a.detected_at.isoformat(),
            }
            for a in anomalies
        ],
        "total": len(anomalies),
    }


@router.post("/projects/{project_id}/anomalies/scan", status_code=201)
async def trigger_anomaly_scan(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user_id),
) -> dict:
    from app.services.anomaly_service import run_anomaly_scan

    detected = await run_anomaly_scan(db, project_id)
    await db.commit()
    return {"detected": len(detected), "anomaly_ids": [str(a.id) for a in detected]}
