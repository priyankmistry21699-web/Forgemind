"""GitHub API rate limiter and retry utilities — FM-160 hardening.

Provides:
- GitHubRateLimiter: tracks GitHub API rate limit headers, signals when to pause
- github_retry: async decorator with exponential backoff for transient GitHub failures
"""

import asyncio
import logging
import time
from functools import wraps
from typing import Any, Callable, TypeVar

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])

# ---------------------------------------------------------------------------
# Rate Limiter
# ---------------------------------------------------------------------------


class GitHubRateLimiter:
    """Track GitHub API rate-limit headers and delay when near the limit.

    Usage:
        limiter = GitHubRateLimiter()
        # After each GitHub API call, feed the response headers:
        limiter.update_from_headers(response.headers)
        # Before the next call:
        await limiter.wait_if_needed()
    """

    def __init__(self, *, remaining_threshold: int = 10) -> None:
        self.remaining: int | None = None
        self.limit: int | None = None
        self.reset_at: float | None = None  # Unix epoch
        self.remaining_threshold = remaining_threshold

    def update_from_headers(self, headers: dict[str, str]) -> None:
        """Parse GitHub rate-limit response headers."""
        if "X-RateLimit-Remaining" in headers:
            self.remaining = int(headers["X-RateLimit-Remaining"])
        if "X-RateLimit-Limit" in headers:
            self.limit = int(headers["X-RateLimit-Limit"])
        if "X-RateLimit-Reset" in headers:
            self.reset_at = float(headers["X-RateLimit-Reset"])

    async def wait_if_needed(self) -> None:
        """Sleep until the rate-limit window resets if remaining is below threshold."""
        if self.remaining is not None and self.remaining <= self.remaining_threshold:
            if self.reset_at is not None:
                wait_seconds = max(0.0, self.reset_at - time.time()) + 1.0
                logger.warning(
                    "GitHub rate limit near threshold (%d remaining). "
                    "Waiting %.1fs until reset.",
                    self.remaining,
                    wait_seconds,
                )
                await asyncio.sleep(wait_seconds)

    @property
    def is_near_limit(self) -> bool:
        return self.remaining is not None and self.remaining <= self.remaining_threshold


# ---------------------------------------------------------------------------
# Retry Decorator
# ---------------------------------------------------------------------------

# HTTP status codes that warrant a retry
_RETRYABLE_STATUSES = {429, 500, 502, 503}


def github_retry(
    *,
    max_attempts: int = 3,
    base_delay: float = 1.0,
    retryable_statuses: set[int] = _RETRYABLE_STATUSES,
) -> Callable[[F], F]:
    """Async retry decorator with exponential backoff for GitHub API calls.

    Retries on:
    - 429 Too Many Requests
    - 500/502/503 transient server errors

    Usage:
        @github_retry(max_attempts=3)
        async def call_github_api(...):
            ...
    """

    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception: Exception | None = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as exc:
                    status_code = getattr(exc, "status_code", None) or getattr(
                        exc, "status", None
                    )
                    if status_code in retryable_statuses and attempt < max_attempts:
                        delay = base_delay * (2 ** (attempt - 1))
                        logger.warning(
                            "GitHub API call %s failed (status %s, attempt %d/%d). "
                            "Retrying in %.1fs.",
                            func.__name__,
                            status_code,
                            attempt,
                            max_attempts,
                            delay,
                        )
                        await asyncio.sleep(delay)
                        last_exception = exc
                    else:
                        raise
            raise last_exception  # type: ignore[misc]

        return wrapper  # type: ignore[return-value]

    return decorator
