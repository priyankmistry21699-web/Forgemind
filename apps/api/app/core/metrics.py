"""Observability metrics - re-exported from forgemind-utils package.

FM-078/FM-079: Code lives in packages/utils; this module provides
backward-compatible imports for existing app code.
"""

from forgemind_utils.metrics import (  # noqa: F401
    inc_counter,
    observe_histogram,
    get_counter,
    render_prometheus,
    reset_metrics,
)

__all__ = [
    "inc_counter",
    "observe_histogram",
    "get_counter",
    "render_prometheus",
    "reset_metrics",
]
