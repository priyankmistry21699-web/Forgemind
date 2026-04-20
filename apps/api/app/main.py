from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.router import api_router
from app.core.rate_limit import RateLimitMiddleware
from app.core.logging_middleware import RequestLoggingMiddleware
from app.core.metrics_middleware import MetricsMiddleware
from app.core.ip_allowlist_middleware import IPAllowlistMiddleware
from app.core.error_handlers import register_error_handlers


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    import asyncio

    # Startup — seed default agents
    from app.db.session import async_session_factory
    from app.services.agent_service import seed_default_agents
    from app.services.project_template_service import seed_builtin_templates
    from app.services.background_scheduler import (
        escalation_loop,
        retention_loop,
        scheduled_report_loop,
    )

    async with async_session_factory() as session:
        await seed_default_agents(session)
        await seed_builtin_templates(session)
        await session.commit()

    # Launch background scheduler tasks (FM-148 / FM-176 / FM-198)
    bg_tasks: list[asyncio.Task] = []
    if not settings.debug:
        bg_tasks.append(asyncio.create_task(escalation_loop(), name="escalation-loop"))
        bg_tasks.append(asyncio.create_task(retention_loop(), name="retention-loop"))
        bg_tasks.append(
            asyncio.create_task(scheduled_report_loop(), name="report-loop")
        )

    yield

    # Shutdown — cancel background tasks, then dispose DB engine
    for task in bg_tasks:
        task.cancel()
    for task in bg_tasks:
        try:
            await task
        except asyncio.CancelledError:
            pass

    from app.db.session import engine

    await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.project_name,
        version=settings.version,
        debug=settings.debug,
        lifespan=lifespan,
    )

    # Global error handlers (FM-050)
    register_error_handlers(app)

    # Middleware stack (order matters: last added = first executed)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Rate limiting (FM-050) — only in non-debug mode
    if not settings.debug:
        app.add_middleware(RateLimitMiddleware, rate_limit=100, window_seconds=60)

    # Request logging (FM-050)
    app.add_middleware(RequestLoggingMiddleware)

    # Metrics collection (FM-078)
    app.add_middleware(MetricsMiddleware)

    # IP allowlist enforcement (FM-178) — checks workspace governance_settings
    app.add_middleware(IPAllowlistMiddleware)

    # Mount routers
    app.include_router(api_router)

    return app


app = create_app()
