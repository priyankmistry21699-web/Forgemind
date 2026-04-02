"""FM-078: Prometheus metrics endpoint."""

from fastapi import APIRouter
from starlette.responses import PlainTextResponse

from app.core.metrics import render_prometheus

router = APIRouter()


@router.get("/metrics", response_class=PlainTextResponse)
async def metrics() -> str:
    """Expose metrics in Prometheus text exposition format."""
    return render_prometheus()
