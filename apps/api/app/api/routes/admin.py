"""FM-215 / FM-216 / FM-217: Admin & observability endpoints.

All endpoints require authentication; operator-level checks are enforced
where workspace context is available.  In dev mode the stub user passes.
"""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query

from app.core.auth import get_current_user_id

router = APIRouter(prefix="/admin", tags=["admin"])


# ---------------------------------------------------------------------------
# FM-215: Slow query stats
# ---------------------------------------------------------------------------


@router.get("/query-stats")
async def get_query_stats(
    limit: int = Query(50, ge=1, le=100),
    _user_id: uuid.UUID = Depends(get_current_user_id),
) -> dict[str, Any]:
    """Return the N most recent slow queries (requires auth)."""
    from app.core.slow_query import get_slow_queries

    entries = get_slow_queries(limit=limit)
    return {
        "count": len(entries),
        "threshold_ms": float(
            __import__("os").getenv("SLOW_QUERY_THRESHOLD_MS", "500")
        ),
        "entries": entries,
    }


# ---------------------------------------------------------------------------
# FM-216: Cache stats
# ---------------------------------------------------------------------------


@router.get("/cache-stats")
async def get_cache_stats(
    _user_id: uuid.UUID = Depends(get_current_user_id),
) -> dict[str, Any]:
    """Return cache hit/miss counters."""
    from app.core.cache import get_cache_stats

    return get_cache_stats()


@router.post("/cache-flush")
async def flush_cache(
    _user_id: uuid.UUID = Depends(get_current_user_id),
) -> dict[str, Any]:
    """Flush in-process cache (does not affect Redis)."""
    from app.core.cache import flush_local_cache

    flushed = flush_local_cache()
    return {"flushed": flushed}


# ---------------------------------------------------------------------------
# FM-217: Background job management
# ---------------------------------------------------------------------------


@router.get("/jobs")
async def list_jobs(
    _user_id: uuid.UUID = Depends(get_current_user_id),
) -> dict[str, Any]:
    """Return recent background job history."""
    from app.worker.job_dispatcher import get_job_history

    return {"jobs": get_job_history()}


@router.post("/jobs/{job_name}/trigger")
async def trigger_job(
    job_name: str,
    _user_id: uuid.UUID = Depends(get_current_user_id),
) -> dict[str, Any]:
    """Manually enqueue a background job by name."""
    from app.worker.job_dispatcher import enqueue_job

    job_id = await enqueue_job(job_name)
    if job_id is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail=f"Unknown job: {job_name}")
    return {"job_id": job_id, "job_name": job_name, "status": "enqueued"}


# ---------------------------------------------------------------------------
# FM-221: Model router status
# ---------------------------------------------------------------------------


@router.get("/model-router/status")
async def model_router_status(
    _user_id: uuid.UUID = Depends(get_current_user_id),
) -> dict[str, Any]:
    """Return current model routing table and selection rationale."""
    from app.core.model_router import get_router_status

    return get_router_status()
