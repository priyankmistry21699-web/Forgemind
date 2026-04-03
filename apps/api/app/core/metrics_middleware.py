"""Metrics middleware — request latency and error tracking.

FM-078: Captures per-route latency histograms, request counters,
and error counters. Uses the lightweight in-memory metrics module.
"""

import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core.metrics import inc_counter, observe_histogram


class MetricsMiddleware(BaseHTTPMiddleware):
    """Capture HTTP request metrics (latency, counts, errors)."""

    async def dispatch(self, request: Request, call_next):
        method = request.method
        path = request.url.path

        start = time.perf_counter()

        try:
            response = await call_next(request)
            elapsed = time.perf_counter() - start

            status = str(response.status_code)
            labels = {"method": method, "path": path, "status": status}

            inc_counter("http_requests_total", labels=labels)
            observe_histogram(
                "http_request_duration_seconds",
                elapsed,
                labels={"method": method, "path": path},
            )

            if response.status_code >= 500:
                inc_counter(
                    "http_errors_total",
                    labels={"method": method, "path": path, "status": status},
                )

            return response
        except Exception:
            elapsed = time.perf_counter() - start
            labels = {"method": method, "path": path, "status": "500"}
            inc_counter("http_requests_total", labels=labels)
            inc_counter("http_errors_total", labels=labels)
            observe_histogram(
                "http_request_duration_seconds",
                elapsed,
                labels={"method": method, "path": path},
            )
            raise
