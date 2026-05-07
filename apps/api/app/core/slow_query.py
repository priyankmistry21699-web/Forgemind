"""FM-215: Slow-query logger with in-memory ring buffer.

Registers SQLAlchemy event listeners on the async engine to detect queries
that exceed SLOW_QUERY_THRESHOLD_MS.  Slow queries are logged as warnings and
stored in a bounded ring buffer (last 100) for the /admin/query-stats endpoint.

Configuration:
    SLOW_QUERY_THRESHOLD_MS  — default 500 ms
    SLOW_QUERY_BUFFER_SIZE   — default 100 entries
"""

from __future__ import annotations

import logging
import os
import time
from collections import deque
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

_THRESHOLD_MS: float = float(os.getenv("SLOW_QUERY_THRESHOLD_MS", "500"))
_BUFFER_SIZE: int = int(os.getenv("SLOW_QUERY_BUFFER_SIZE", "100"))

# Thread-safe-enough for asyncio single-thread usage
_slow_query_buffer: deque[dict[str, Any]] = deque(maxlen=_BUFFER_SIZE)

# Per-connection query start times keyed by (connection, statement id)
_query_start: dict[int, float] = {}


def _before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """Record query start time."""
    _query_start[id(cursor)] = time.perf_counter()


def _after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """Check elapsed time; log and record if slow."""
    start = _query_start.pop(id(cursor), None)
    if start is None:
        return
    elapsed_ms = (time.perf_counter() - start) * 1000
    if elapsed_ms >= _THRESHOLD_MS:
        # Truncate long statements for storage
        stmt_preview = statement.strip()[:500]
        entry: dict[str, Any] = {
            "statement": stmt_preview,
            "elapsed_ms": round(elapsed_ms, 2),
            "recorded_at": datetime.now(timezone.utc).isoformat(),
        }
        _slow_query_buffer.append(entry)
        logger.warning(
            "slow_query detected: %.1fms | %s",
            elapsed_ms,
            stmt_preview[:120],
        )


def install_slow_query_listener(engine) -> None:
    """Attach event listeners to a SQLAlchemy engine.

    Works with both sync and async engines — async engines expose a
    .sync_engine attribute.
    """
    from sqlalchemy import event

    target = getattr(engine, "sync_engine", engine)
    event.listen(target, "before_cursor_execute", _before_cursor_execute)
    event.listen(target, "after_cursor_execute", _after_cursor_execute)
    logger.info(
        "slow_query: listener installed (threshold=%.0fms, buffer=%d)",
        _THRESHOLD_MS,
        _BUFFER_SIZE,
    )


def get_slow_queries(*, limit: int = 50) -> list[dict[str, Any]]:
    """Return the most recent slow queries (newest first)."""
    items = list(_slow_query_buffer)
    items.reverse()
    return items[:limit]


def clear_slow_queries() -> None:
    """Clear the ring buffer (useful in tests)."""
    _slow_query_buffer.clear()
