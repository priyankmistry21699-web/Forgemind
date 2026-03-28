"""FM-054: Server-Sent Events streaming endpoint."""

import asyncio

from fastapi import APIRouter
from starlette.responses import StreamingResponse

router = APIRouter()


async def _event_generator():
    """Yield periodic heartbeat events (placeholder for real event bus)."""
    while True:
        yield "event: heartbeat\ndata: {}\n\n"
        await asyncio.sleep(15)


@router.get("/stream/events")
async def stream_events() -> StreamingResponse:
    return StreamingResponse(
        _event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
