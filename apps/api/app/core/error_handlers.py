"""Global error handlers - re-exported from forgemind-utils package.

FM-050/FM-079: Code lives in packages/utils; this module provides
backward-compatible imports for existing app code.
"""

from forgemind_utils.error_handlers import register_error_handlers  # noqa: F401

__all__ = ["register_error_handlers"]
