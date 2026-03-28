"""FM-054: Server-Sent Events streaming endpoints.

Supports both global event streaming and run-scoped subscriptions.
"""

import asyncio
import uuid

from fastapi import APIRouter
from starlette.responses import StreamingResponse

from app.services.stream_service import (
    run_event_generator,
    global_event_generator,
)

router = APIRouter()


async def _event_generator():
    """Yield periodic heartbeat events (placeholder for real event bus)."""
    while True:
        yield "event: heartbeat\ndata: {}\n\n"
        await asyncio.sleep(15)


@router.get("/stream/events")
async def stream_events() -> StreamingResponse:
    """Global SSE stream — heartbeats and cross-run events."""
    return StreamingResponse(
        global_event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/runs/{run_id}/stream")
async def stream_run_events(run_id: uuid.UUID) -> StreamingResponse:
    """Run-scoped SSE stream — real-time task, approval, artifact events."""
    return StreamingResponse(
        run_event_generator(run_id),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
