"""Background scheduler — periodic tasks for escalation and retention.

FM-148: Auto-escalate expired approvals on a schedule.
FM-176: Evaluate retention policies across all active workspaces.

Uses asyncio tasks launched from the FastAPI lifespan — no external
broker dependency (Celery/APScheduler) required.
"""

import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import select

logger = logging.getLogger(__name__)

# Default intervals (seconds). Override via environment or settings.
ESCALATION_INTERVAL_SECONDS = 300  # 5 minutes
RETENTION_INTERVAL_SECONDS = 86_400  # 24 hours


async def _run_escalation_cycle() -> dict:
    """Execute one escalation cycle: deactivate expired delegations, then
    escalate expired approvals."""
    from app.db.session import async_session_factory
    from app.services import approval_enhanced_service

    async with async_session_factory() as db:
        deactivated = await approval_enhanced_service.deactivate_expired_delegations(db)
        report = await approval_enhanced_service.escalate_expired_approvals(db)
        await db.commit()

    return {
        "delegations_deactivated": deactivated,
        "approvals_escalated": len(report),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


async def _run_retention_cycle() -> dict:
    """Evaluate retention policies for every active workspace."""
    from app.db.session import async_session_factory
    from app.models.workspace import Workspace

    results: list[dict] = []

    async with async_session_factory() as db:
        ws_q = select(Workspace.id)
        workspace_ids = (await db.execute(ws_q)).scalars().all()

    for ws_id in workspace_ids:
        async with async_session_factory() as db:
            from app.services import retention_policy_service

            report = await retention_policy_service.evaluate_retention(
                db, ws_id, dry_run=False,
            )
            await db.commit()
            results.append(report)

    return {
        "workspaces_evaluated": len(results),
        "total_deleted": sum(r.get("total_deleted", 0) for r in results),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


async def escalation_loop() -> None:
    """Background loop: periodically runs auto-escalation."""
    logger.info(
        "background_scheduler: escalation loop started (interval=%ds)",
        ESCALATION_INTERVAL_SECONDS,
    )
    while True:
        try:
            await asyncio.sleep(ESCALATION_INTERVAL_SECONDS)
            result = await _run_escalation_cycle()
            if result["approvals_escalated"] or result["delegations_deactivated"]:
                logger.info("background_scheduler: escalation cycle result=%s", result)
        except asyncio.CancelledError:
            logger.info("background_scheduler: escalation loop cancelled")
            break
        except Exception:
            logger.exception("background_scheduler: escalation cycle failed")


async def retention_loop() -> None:
    """Background loop: periodically runs retention evaluation."""
    logger.info(
        "background_scheduler: retention loop started (interval=%ds)",
        RETENTION_INTERVAL_SECONDS,
    )
    while True:
        try:
            await asyncio.sleep(RETENTION_INTERVAL_SECONDS)
            result = await _run_retention_cycle()
            if result["total_deleted"]:
                logger.info("background_scheduler: retention cycle result=%s", result)
        except asyncio.CancelledError:
            logger.info("background_scheduler: retention loop cancelled")
            break
        except Exception:
            logger.exception("background_scheduler: retention cycle failed")
