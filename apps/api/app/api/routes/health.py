"""FM-214: Extended health & readiness probes for Kubernetes + monitoring."""

import time

from fastapi import APIRouter, Depends, Response, status as http_status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.config import settings

router = APIRouter()


@router.get("/health")
async def health_check() -> dict:
    return {
        "status": "healthy",
        "service": "forgemind-api",
        "version": settings.version,
    }


@router.get("/health/live")
async def liveness_check() -> dict:
    """Kubernetes liveness probe — always 200 if process is running."""
    return {"status": "alive", "service": "forgemind-api"}


@router.get("/health/ready")
async def readiness_check(db: AsyncSession = Depends(get_db)) -> dict:
    """Kubernetes readiness probe — checks DB connectivity."""
    await db.execute(text("SELECT 1"))
    return {
        "status": "ready",
        "service": "forgemind-api",
        "database": "connected",
    }


@router.get("/health/dependencies")
async def dependency_check(
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Deep health check — measures latency of every external dependency.

    Returns 503 if any critical dependency (postgres, redis) is unreachable.
    """
    results: dict = {}
    all_healthy = True

    # PostgreSQL
    t0 = time.perf_counter()
    try:
        await db.execute(text("SELECT 1"))
        results["postgres"] = {
            "status": "ok",
            "latency_ms": round((time.perf_counter() - t0) * 1000, 1),
        }
    except Exception as exc:
        results["postgres"] = {"status": "error", "detail": str(exc)}
        all_healthy = False

    # Redis
    t0 = time.perf_counter()
    try:
        import redis.asyncio as aioredis

        r = aioredis.from_url(settings.redis_url, socket_connect_timeout=2)
        await r.ping()
        await r.aclose()
        results["redis"] = {
            "status": "ok",
            "latency_ms": round((time.perf_counter() - t0) * 1000, 1),
        }
    except Exception as exc:
        results["redis"] = {"status": "error", "detail": str(exc)}
        all_healthy = False

    if not all_healthy:
        response.status_code = http_status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": "healthy" if all_healthy else "degraded",
        "service": "forgemind-api",
        "dependencies": results,
    }
