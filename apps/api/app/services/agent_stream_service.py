"""FM-224: Streaming agent output service.

Workers publish agent step events to a Redis channel;
the API subscribes and forwards them as SSE to the browser.

Channel naming: fm:run:{run_id}:stream

Event types:
    agent_step_start   — {"agent": "coder", "task_id": "...", "task_title": "..."}
    agent_step_chunk   — {"chunk": "partial text", "seq": 0}
    agent_step_done    — {"artifact_type": "implementation", "elapsed_ms": 1234}
    run_done           — {"status": "completed"}
    run_error          — {"error": "message"}
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from collections.abc import AsyncGenerator
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

_STREAM_TTL_SECONDS = 300  # Redis channel TTL after last message


def _channel_key(run_id: uuid.UUID) -> str:
    return f"fm:run:{run_id}:stream"


# ---------------------------------------------------------------------------
# Publisher (called from worker / background tasks)
# ---------------------------------------------------------------------------


async def publish_event(
    run_id: uuid.UUID,
    event_type: str,
    payload: dict,
    *,
    redis_url: str | None = None,
) -> None:
    """Publish an agent stream event to Redis pub/sub."""
    try:
        import redis.asyncio as aioredis
        from app.core.config import settings

        r = aioredis.from_url(
            redis_url or settings.redis_url,
            socket_connect_timeout=1,
        )
        message = json.dumps(
            {
                "type": event_type,
                "run_id": str(run_id),
                "ts": datetime.now(timezone.utc).isoformat(),
                **payload,
            }
        )
        await r.publish(_channel_key(run_id), message)
        await r.aclose()
    except Exception as exc:
        logger.debug("agent_stream: publish failed (%s) — SSE won't update", exc)


# ---------------------------------------------------------------------------
# Subscriber (called from SSE route)
# ---------------------------------------------------------------------------


async def stream_run_events(
    run_id: uuid.UUID,
    *,
    redis_url: str | None = None,
    timeout_seconds: int = 300,
) -> AsyncGenerator[str, None]:
    """Async generator yielding SSE-formatted strings for a run.

    Falls back to a simple polling approach when Redis is unavailable.
    """
    try:
        import redis.asyncio as aioredis
        from app.core.config import settings

        r = aioredis.from_url(redis_url or settings.redis_url, socket_connect_timeout=2)
        pubsub = r.pubsub()
        await pubsub.subscribe(_channel_key(run_id))

        try:
            deadline = asyncio.get_event_loop().time() + timeout_seconds
            while asyncio.get_event_loop().time() < deadline:
                try:
                    message = await asyncio.wait_for(
                        pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0),
                        timeout=2.0,
                    )
                except asyncio.TimeoutError:
                    yield ": heartbeat\n\n"
                    continue

                if message is None:
                    yield ": heartbeat\n\n"
                    await asyncio.sleep(0.1)
                    continue

                data = message.get("data", "")
                if isinstance(data, bytes):
                    data = data.decode()

                yield f"data: {data}\n\n"

                # Stop streaming when the run finishes
                try:
                    parsed = json.loads(data)
                    if parsed.get("type") in ("run_done", "run_error"):
                        break
                except Exception:
                    pass
        finally:
            await pubsub.unsubscribe(_channel_key(run_id))
            await r.aclose()

    except Exception as exc:
        logger.info("agent_stream: Redis unavailable (%s) — serving stub stream", exc)
        # Fallback: emit a single status event from DB
        yield f"data: {json.dumps({'type': 'error', 'error': 'Redis unavailable'})}\n\n"
