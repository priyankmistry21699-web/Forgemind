"""Stream service — in-memory event pub/sub for SSE streaming.

FM-054: Provides run-scoped event publishing and subscription for real-time
updates via Server-Sent Events. Uses asyncio.Queue for fan-out to subscribers.
"""

import asyncio
import json
import logging
import uuid
from collections import defaultdict
from typing import Any, AsyncGenerator

logger = logging.getLogger(__name__)

# ── In-memory subscriber registry ───────────────────────────────
# run_id -> list of asyncio.Queue
_subscribers: dict[uuid.UUID, list[asyncio.Queue]] = defaultdict(list)
_global_subscribers: list[asyncio.Queue] = []


def subscribe_run(run_id: uuid.UUID) -> asyncio.Queue:
    """Subscribe to events for a specific run. Returns a Queue to await on."""
    queue: asyncio.Queue = asyncio.Queue(maxsize=100)
    _subscribers[run_id].append(queue)
    logger.debug("New subscriber for run %s (total: %d)", run_id, len(_subscribers[run_id]))
    return queue


def unsubscribe_run(run_id: uuid.UUID, queue: asyncio.Queue) -> None:
    """Remove a subscriber from a run's event stream."""
    if run_id in _subscribers:
        try:
            _subscribers[run_id].remove(queue)
        except ValueError:
            pass
        if not _subscribers[run_id]:
            del _subscribers[run_id]


def subscribe_global() -> asyncio.Queue:
    """Subscribe to all events across all runs."""
    queue: asyncio.Queue = asyncio.Queue(maxsize=100)
    _global_subscribers.append(queue)
    return queue


def unsubscribe_global(queue: asyncio.Queue) -> None:
    """Remove a global subscriber."""
    try:
        _global_subscribers.remove(queue)
    except ValueError:
        pass


async def publish_run_event(
    run_id: uuid.UUID,
    event_type: str,
    data: dict[str, Any],
) -> int:
    """Publish an event to all subscribers of a specific run.

    Returns the number of subscribers notified.
    """
    payload = {
        "run_id": str(run_id),
        "event_type": event_type,
        "data": data,
    }

    notified = 0

    # Run-specific subscribers
    for queue in list(_subscribers.get(run_id, [])):
        try:
            queue.put_nowait(payload)
            notified += 1
        except asyncio.QueueFull:
            logger.warning("Subscriber queue full for run %s, dropping event", run_id)

    # Global subscribers
    for queue in list(_global_subscribers):
        try:
            queue.put_nowait(payload)
            notified += 1
        except asyncio.QueueFull:
            logger.warning("Global subscriber queue full, dropping event")

    return notified


async def run_event_generator(run_id: uuid.UUID) -> AsyncGenerator[str, None]:
    """Async generator that yields SSE-formatted events for a run.

    Sends heartbeats every 15 seconds to keep the connection alive.
    """
    queue = subscribe_run(run_id)
    try:
        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=15.0)
                yield f"event: {event['event_type']}\ndata: {json.dumps(event['data'])}\n\n"
            except asyncio.TimeoutError:
                yield "event: heartbeat\ndata: {}\n\n"
    finally:
        unsubscribe_run(run_id, queue)


async def global_event_generator() -> AsyncGenerator[str, None]:
    """Async generator that yields SSE-formatted events from all runs.

    Sends heartbeats every 15 seconds.
    """
    queue = subscribe_global()
    try:
        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=15.0)
                yield f"event: {event['event_type']}\ndata: {json.dumps(event['data'])}\n\n"
            except asyncio.TimeoutError:
                yield "event: heartbeat\ndata: {}\n\n"
    finally:
        unsubscribe_global(queue)
