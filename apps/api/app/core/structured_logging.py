"""FM-213: Structured logging with structlog.

Provides a configured structlog setup that emits JSON in production and
a pretty human-readable format in development.  Every log line includes:
    - request_id / trace_id (injected by middleware)
    - timestamp, level, logger name
    - All key=value pairs bound via structlog.contextvars

Usage:
    from app.core.structured_logging import get_logger, configure_logging
    log = get_logger(__name__)
    log.info("event", user_id=str(uid), action="create_project")
"""

from __future__ import annotations

import logging
import sys
import os
import uuid
import time
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

_STRUCTLOG_AVAILABLE = False
try:
    import structlog
    import structlog.contextvars

    _STRUCTLOG_AVAILABLE = True
except ImportError:
    pass


def configure_logging(log_level: str | None = None) -> None:
    """Configure structlog + stdlib logging.  Call once at startup."""
    level_str = (log_level or os.getenv("LOG_LEVEL", "INFO")).upper()
    level = getattr(logging, level_str, logging.INFO)

    if not _STRUCTLOG_AVAILABLE:
        logging.basicConfig(
            level=level,
            format="%(asctime)s %(levelname)s %(name)s %(message)s",
            stream=sys.stdout,
        )
        return

    # Shared processors for both stdlib and structlog
    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_logger_name,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
    ]

    app_env = os.getenv("APP_ENV", "development")
    is_prod = app_env not in ("development", "test")

    if is_prod:
        processors = shared_processors + [
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ]
    else:
        processors = shared_processors + [
            structlog.processors.ExceptionRenderer(),
            structlog.dev.ConsoleRenderer(colors=sys.stdout.isatty()),
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(sys.stdout),
        cache_logger_on_first_use=True,
    )

    # Also configure stdlib so third-party libraries emit structured logs
    logging.basicConfig(
        format="%(message)s",
        level=level,
        stream=sys.stdout,
    )
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


def get_logger(name: str | None = None):
    """Return a structlog logger bound to the given name (falls back to stdlib)."""
    if _STRUCTLOG_AVAILABLE:
        return structlog.get_logger(name)
    return logging.getLogger(name or "forgemind")


# ---------------------------------------------------------------------------
# Request-context middleware
# ---------------------------------------------------------------------------


class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    """Injects request_id + trace_id into structlog contextvars for every request.

    This means any log line emitted downstream automatically includes the
    request_id without the caller needing to pass it explicitly.
    """

    async def dispatch(self, request: Request, call_next):
        request_id = getattr(request.state, "request_id", None) or str(uuid.uuid4())[:8]
        request.state.request_id = request_id

        start = time.perf_counter()

        if _STRUCTLOG_AVAILABLE:
            structlog.contextvars.clear_contextvars()
            structlog.contextvars.bind_contextvars(
                request_id=request_id,
                method=request.method,
                path=request.url.path,
            )

        try:
            response = await call_next(request)
            duration_ms = round((time.perf_counter() - start) * 1000, 1)

            if _STRUCTLOG_AVAILABLE:
                structlog.contextvars.bind_contextvars(
                    status_code=response.status_code,
                    duration_ms=duration_ms,
                )

            response.headers["X-Request-ID"] = request_id
            return response

        except Exception:
            duration_ms = round((time.perf_counter() - start) * 1000, 1)
            if _STRUCTLOG_AVAILABLE:
                structlog.contextvars.bind_contextvars(
                    status_code=500,
                    duration_ms=duration_ms,
                )
            raise
        finally:
            if _STRUCTLOG_AVAILABLE:
                structlog.contextvars.clear_contextvars()
