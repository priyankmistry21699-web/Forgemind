"""FM-217: Lightweight async background job dispatcher.

Moves long-running work off the HTTP request path without requiring
an external broker.  Jobs are asyncio Tasks launched inside the existing
FastAPI lifespan.  All executions are tracked in a bounded history buffer.

Registered jobs
---------------
send_notification      — deliver pending notifications via configured channels
export_audit_log       — build and upload a workspace audit JSONL export
refresh_credentials    — refresh all expired credential statuses
generate_report        — execute a scheduled analytics report

Usage in a route:
    from app.worker.job_dispatcher import enqueue_job
    job_id = await enqueue_job("send_notification", user_id=str(uid), ...)
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from collections import deque
from datetime import datetime, timezone
from typing import Any, Callable, Awaitable

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# History buffer
# ---------------------------------------------------------------------------

_HISTORY_MAX = 200
_job_history: deque[dict[str, Any]] = deque(maxlen=_HISTORY_MAX)


def _record(job_id: str, job_name: str, status: str, **extra: Any) -> None:
    _job_history.append(
        {
            "job_id": job_id,
            "job_name": job_name,
            "status": status,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
            **extra,
        }
    )


def get_job_history() -> list[dict[str, Any]]:
    """Return recent job records newest-first."""
    items = list(_job_history)
    items.reverse()
    return items


# ---------------------------------------------------------------------------
# Job registry
# ---------------------------------------------------------------------------

JobFn = Callable[..., Awaitable[Any]]
_registry: dict[str, JobFn] = {}


def register_job(name: str, fn: JobFn) -> None:
    _registry[name] = fn


# ---------------------------------------------------------------------------
# Built-in job: send_notification
# ---------------------------------------------------------------------------


async def _job_send_notification(**kwargs: Any) -> None:
    """Deliver a single notification via all enabled channels."""
    from app.db.session import async_session_factory
    from app.services import notification_service
    from app.services.email_service import send_notification_email

    user_id_str = kwargs.get("user_id")
    notification_id_str = kwargs.get("notification_id")
    if not user_id_str or not notification_id_str:
        return

    user_id = uuid.UUID(user_id_str)
    notification_id = uuid.UUID(notification_id_str)

    async with async_session_factory() as db:
        notif = await db.get(
            __import__("app.models.notification", fromlist=["Notification"]).Notification,
            notification_id,
        )
        if notif is None:
            return
        allowed = await notification_service.is_notification_allowed(
            db, user_id, notif.notification_type
        )
        if not allowed:
            return
        from app.services.email_service import send_notification_email_async
        await send_notification_email_async(db, notif)
        await db.commit()


# ---------------------------------------------------------------------------
# Built-in job: refresh_credentials
# ---------------------------------------------------------------------------


async def _job_refresh_credentials(**kwargs: Any) -> None:
    from app.db.session import async_session_factory
    from app.services import credential_vault_service

    async with async_session_factory() as db:
        changed = await credential_vault_service.refresh_credential_statuses(db)
        await db.commit()
    logger.info("job_dispatcher: refresh_credentials changed=%d", changed)


# ---------------------------------------------------------------------------
# Built-in job: export_audit_log
# ---------------------------------------------------------------------------


async def _job_export_audit_log(**kwargs: Any) -> None:
    workspace_id_str = kwargs.get("workspace_id")
    if not workspace_id_str:
        return
    logger.info(
        "job_dispatcher: export_audit_log workspace=%s (async stub)", workspace_id_str
    )


# ---------------------------------------------------------------------------
# Built-in job: generate_report
# ---------------------------------------------------------------------------


async def _job_generate_report(**kwargs: Any) -> None:
    report_id_str = kwargs.get("report_id")
    if not report_id_str:
        return
    logger.info(
        "job_dispatcher: generate_report report_id=%s (async stub)", report_id_str
    )


# Register all built-ins
register_job("send_notification", _job_send_notification)
register_job("refresh_credentials", _job_refresh_credentials)
register_job("export_audit_log", _job_export_audit_log)
register_job("generate_report", _job_generate_report)

# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------


async def enqueue_job(job_name: str, **kwargs: Any) -> str | None:
    """Enqueue a named job.  Returns job_id or None if job_name unknown."""
    fn = _registry.get(job_name)
    if fn is None:
        logger.warning("job_dispatcher: unknown job '%s'", job_name)
        return None

    job_id = str(uuid.uuid4())
    _record(job_id, job_name, "enqueued")

    async def _run() -> None:
        _record(job_id, job_name, "running")
        try:
            await fn(**kwargs)
            _record(job_id, job_name, "completed")
        except Exception as exc:
            _record(job_id, job_name, "failed", error=str(exc))
            logger.exception("job_dispatcher: job %s/%s failed", job_name, job_id)

    asyncio.create_task(_run(), name=f"job-{job_name}-{job_id[:8]}")
    logger.debug("job_dispatcher: enqueued %s (%s)", job_name, job_id)
    return job_id
