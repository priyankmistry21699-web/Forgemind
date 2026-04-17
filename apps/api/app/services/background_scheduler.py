"""Background scheduler — periodic tasks for escalation, retention, and reports.

FM-148: Auto-escalate expired approvals on a schedule.
FM-176: Evaluate retention policies across all active workspaces.
FM-198: Execute scheduled reports when their cron expression matches.

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
REPORT_CHECK_INTERVAL_SECONDS = 60  # check every minute


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


# ── FM-198: Scheduled Reports ────────────────────────────────────


def _cron_matches_now(cron_expr: str, now: datetime) -> bool:
    """Check whether a 5-field cron expression matches the given minute.

    Supports: ``*``, literal numbers, comma-separated lists,
    ranges (``1-5``), and step (``*/10``).
    Fields: minute hour day-of-month month day-of-week.
    """
    parts = cron_expr.strip().split()
    if len(parts) < 5:
        return False

    actuals = [now.minute, now.hour, now.day, now.month, now.isoweekday() % 7]

    for field, actual in zip(parts[:5], actuals):
        if field == "*":
            continue
        if "/" in field:
            base, step = field.split("/", 1)
            try:
                step_int = int(step)
            except ValueError:
                return False
            if step_int <= 0:
                return False
            if actual % step_int != 0:
                return False
            continue
        # Comma-separated or range
        matched = False
        for token in field.split(","):
            if "-" in token:
                lo, hi = token.split("-", 1)
                try:
                    if int(lo) <= actual <= int(hi):
                        matched = True
                        break
                except ValueError:
                    pass
            else:
                try:
                    if int(token) == actual:
                        matched = True
                        break
                except ValueError:
                    pass
        if not matched:
            return False

    return True


async def _run_scheduled_reports_cycle() -> dict:
    """Check all active scheduled reports and execute those whose cron matches."""
    from app.db.session import async_session_factory
    from app.models.analytics_metrics import ScheduledReport
    from app.services import dashboard_alert_service

    now = datetime.now(timezone.utc)
    executed = 0

    async with async_session_factory() as db:
        result = await db.execute(
            select(ScheduledReport).where(ScheduledReport.active.is_(True))
        )
        reports = list(result.scalars().all())

        for report in reports:
            if not _cron_matches_now(report.schedule_cron, now):
                continue

            # Avoid re-running within the same minute
            if (
                report.last_generated_at
                and (now - report.last_generated_at).total_seconds() < 60
            ):
                continue

            try:
                # Reports require a project_id context.  Use org_id as a
                # project search scope — execute for *each* project linked
                # to the org if available.  If no org_id, skip gracefully.
                await dashboard_alert_service.execute_scheduled_report(
                    db, report.id, project_id=report.org_id or report.id,
                )
                executed += 1
            except Exception:
                logger.warning(
                    "background_scheduler: report %s execution failed",
                    report.id,
                    exc_info=True,
                )

        await db.commit()

    return {
        "reports_checked": len(reports),
        "reports_executed": executed,
        "timestamp": now.isoformat(),
    }


async def scheduled_report_loop() -> None:
    """Background loop: check and execute scheduled reports every minute."""
    logger.info(
        "background_scheduler: scheduled-report loop started (interval=%ds)",
        REPORT_CHECK_INTERVAL_SECONDS,
    )
    while True:
        try:
            await asyncio.sleep(REPORT_CHECK_INTERVAL_SECONDS)
            result = await _run_scheduled_reports_cycle()
            if result["reports_executed"]:
                logger.info(
                    "background_scheduler: report cycle result=%s", result
                )
        except asyncio.CancelledError:
            logger.info("background_scheduler: report loop cancelled")
            break
        except Exception:
            logger.exception("background_scheduler: report cycle failed")
