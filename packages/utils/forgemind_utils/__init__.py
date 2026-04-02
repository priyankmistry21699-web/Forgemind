"""forgemind-utils — Shared utilities for the ForgeMind platform.

Provides reusable middleware, metrics, rate limiting, and error handling.
"""

from forgemind_utils.metrics import inc_counter, observe_histogram, get_counter, render_prometheus, reset_metrics
from forgemind_utils.rate_limit import RateLimitMiddleware
from forgemind_utils.error_handlers import register_error_handlers
from forgemind_utils.logging_middleware import RequestLoggingMiddleware

__all__ = [
    "inc_counter",
    "observe_histogram",
    "get_counter",
    "render_prometheus",
    "reset_metrics",
    "RateLimitMiddleware",
    "register_error_handlers",
    "RequestLoggingMiddleware",
]
