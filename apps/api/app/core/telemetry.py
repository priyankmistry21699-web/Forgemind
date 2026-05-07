"""FM-212: OpenTelemetry distributed tracing.

Instruments FastAPI + SQLAlchemy when opentelemetry-sdk is installed.
Gracefully no-ops when the SDK is absent so tests never fail due to a
missing optional dependency.

Configure via environment variables:
    OTEL_SERVICE_NAME      — default "forgemind-api"
    OTEL_EXPORTER_OTLP_ENDPOINT — e.g. "http://jaeger:4318" (blank = no export)
    OTEL_ENABLED           — set to "false" to disable even if SDK is installed
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

if TYPE_CHECKING:
    from fastapi import FastAPI

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional SDK import
# ---------------------------------------------------------------------------

_OTEL_AVAILABLE = False
_tracer = None

try:
    import opentelemetry  # noqa: F401

    _OTEL_AVAILABLE = True
except ImportError:
    pass


def setup_telemetry(app: "FastAPI | None" = None) -> None:
    """Configure OpenTelemetry tracing.  Safe to call even when SDK absent."""
    global _tracer

    import os

    if os.getenv("OTEL_ENABLED", "true").lower() == "false":
        logger.info("telemetry: OTEL_ENABLED=false — skipping setup")
        return

    if not _OTEL_AVAILABLE:
        logger.info(
            "telemetry: opentelemetry-sdk not installed — tracing disabled. "
            "Install with: pip install opentelemetry-sdk opentelemetry-instrumentation-fastapi"
        )
        return

    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.resources import Resource, SERVICE_NAME

    service_name = os.getenv("OTEL_SERVICE_NAME", "forgemind-api")
    resource = Resource.create({SERVICE_NAME: service_name})
    provider = TracerProvider(resource=resource)

    # OTLP export (optional)
    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "")
    if otlp_endpoint:
        try:
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
                OTLPSpanExporter,
            )
            from opentelemetry.sdk.trace.export import BatchSpanProcessor

            exporter = OTLPSpanExporter(
                endpoint=f"{otlp_endpoint.rstrip('/')}/v1/traces"
            )
            provider.add_span_processor(BatchSpanProcessor(exporter))
            logger.info("telemetry: OTLP exporter → %s", otlp_endpoint)
        except ImportError:
            logger.warning(
                "telemetry: opentelemetry-exporter-otlp not installed — no OTLP export"
            )

    trace.set_tracer_provider(provider)
    _tracer = trace.get_tracer(service_name)

    # Instrument FastAPI
    if app is not None:
        try:
            from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

            FastAPIInstrumentor.instrument_app(app)
            logger.info("telemetry: FastAPI instrumented")
        except ImportError:
            pass

    # Instrument SQLAlchemy
    try:
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

        SQLAlchemyInstrumentor().instrument()
        logger.info("telemetry: SQLAlchemy instrumented")
    except ImportError:
        pass

    logger.info("telemetry: setup complete (service=%s)", service_name)


def get_tracer():
    """Return the global tracer (may be None if OTel is not configured)."""
    return _tracer


def current_trace_id() -> str | None:
    """Return the current span's trace ID as a hex string, or None."""
    if not _OTEL_AVAILABLE:
        return None
    try:
        from opentelemetry import trace

        span = trace.get_current_span()
        ctx = span.get_span_context()
        if ctx and ctx.is_valid:
            return format(ctx.trace_id, "032x")
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# Trace-ID response header middleware
# ---------------------------------------------------------------------------


class TraceIDMiddleware(BaseHTTPMiddleware):
    """Attach X-Trace-ID to every response.

    Uses the active OTel trace ID when available; falls back to the
    request_id already set by RequestLoggingMiddleware.
    """

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        tid = current_trace_id()
        if tid:
            response.headers["X-Trace-ID"] = tid
        else:
            # Fall back to request_id set by RequestLoggingMiddleware
            rid = getattr(request.state, "request_id", None)
            if rid:
                response.headers["X-Trace-ID"] = rid

        return response
