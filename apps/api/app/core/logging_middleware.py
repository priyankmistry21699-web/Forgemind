"""Request logging middleware — structured request/response logging.

FM-050: Logs every request with timing, status code, and path.
"""

import time
import logging
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger("forgemind.access")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log every request with timing and status information."""

    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())[:8]
        start = time.perf_counter()

        # Attach request_id to state for downstream use
        request.state.request_id = request_id

        try:
            response = await call_next(request)
            elapsed_ms = (time.perf_counter() - start) * 1000

            logger.info(
                "[%s] %s %s → %d (%.1fms)",
                request_id,
                request.method,
                request.url.path,
                response.status_code,
                elapsed_ms,
            )

            response.headers["X-Request-ID"] = request_id
            return response

        except Exception as exc:
            elapsed_ms = (time.perf_counter() - start) * 1000
            logger.error(
                "[%s] %s %s → ERROR (%.1fms): %s",
                request_id,
                request.method,
                request.url.path,
                elapsed_ms,
                str(exc),
            )
            raise
