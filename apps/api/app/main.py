from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.router import api_router
from app.core.rate_limit import RateLimitMiddleware
from app.core.logging_middleware import RequestLoggingMiddleware
from app.core.error_handlers import register_error_handlers


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    # Startup — seed default agents
    from app.db.session import async_session_factory
    from app.services.agent_service import seed_default_agents

    async with async_session_factory() as session:
        await seed_default_agents(session)
        await session.commit()

    yield
    # Shutdown — dispose DB engine
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

    # Mount routers
    app.include_router(api_router)

    return app


app = create_app()
