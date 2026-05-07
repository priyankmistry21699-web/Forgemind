"""FM-078: Prometheus metrics endpoint."""

import uuid

from fastapi import APIRouter, Depends
from starlette.responses import PlainTextResponse

from app.core.auth import get_current_user_id
from app.core.metrics import render_prometheus

router = APIRouter()


# H-8: Prometheus scrapers must use a service-account JWT; unauthenticated
# access would expose internal usage counters to external callers.
@router.get("/metrics", response_class=PlainTextResponse)
async def metrics(
    _user_id: uuid.UUID = Depends(get_current_user_id),
) -> str:
    """Expose metrics in Prometheus text exposition format."""
    return render_prometheus()
