"""Rate limiting middleware - re-exported from forgemind-utils package.

FM-050/FM-079: Code lives in packages/utils; this module provides
backward-compatible imports for existing app code.
"""

from forgemind_utils.rate_limit import RateLimitMiddleware, _TokenBucket  # noqa: F401

__all__ = ["RateLimitMiddleware", "_TokenBucket"]
