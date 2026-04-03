"""Request logging middleware - re-exported from forgemind-utils package.

FM-050/FM-079: Code lives in packages/utils; this module provides
backward-compatible imports for existing app code.
"""

from forgemind_utils.logging_middleware import RequestLoggingMiddleware  # noqa: F401

__all__ = ["RequestLoggingMiddleware"]
