"""Dashboard stats overview endpoint — live counts for the UI stat cards."""

import time
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user_id
from app.db.session import get_db
from app.services import task_service, approval_service

router = APIRouter()


@router.get("/stats/overview")
async def stats_overview(
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> dict:
    """Return live counts for the dashboard: running tasks, pending approvals, health."""
    running_tasks = await task_service.count_running_tasks(db)
    pending_approvals = await approval_service.count_pending_for_user(db, user_id)

    # Quick DB liveness check (reuses the same session — no extra connection)
    t0 = time.perf_counter()
    healthy = True
    try:
        await db.execute(text("SELECT 1"))
        db_latency_ms = round((time.perf_counter() - t0) * 1000, 1)
    except Exception:
        healthy = False
        db_latency_ms = None

    return {
        "running_tasks": running_tasks,
        "pending_approvals": pending_approvals,
        "healthy": healthy,
        "db_latency_ms": db_latency_ms,
    }
