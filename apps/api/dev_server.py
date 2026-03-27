"""
ForgeMind — Lightweight dev server using SQLite.

Run with:
    python dev_server.py

Starts the API on http://localhost:8000 with an on-disk SQLite database
(dev.db) so no Docker/PostgreSQL is required for UI development.
"""

import asyncio
import uuid

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID as PG_UUID, JSON as PG_JSON
from sqlalchemy import Uuid, JSON
from sqlalchemy.ext.compiler import compiles

# ── Patch PostgreSQL types for SQLite ──────────────────────────
@compiles(ARRAY, "sqlite")
def _compile_array_sqlite(type_, compiler, **kw):
    return "JSON"

from app.db.base_class import Base
from app.db.base import *  # noqa: F401, F403

def _patch_metadata_for_sqlite():
    for table in Base.metadata.tables.values():
        for column in table.columns:
            if isinstance(column.type, PG_UUID):
                column.type = Uuid(as_uuid=True)
            elif isinstance(column.type, ARRAY):
                column.type = JSON()
            elif isinstance(column.type, PG_JSON):
                column.type = JSON()

_patch_metadata_for_sqlite()

# ── SQLite dev database ────────────────────────────────────────
DEV_DATABASE_URL = "sqlite+aiosqlite:///dev.db"

dev_engine = create_async_engine(
    DEV_DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
)

dev_session_factory = async_sessionmaker(
    dev_engine, class_=AsyncSession, expire_on_commit=False,
)

# ── Override app dependencies ──────────────────────────────────
from app.db.session import get_db
from app.main import create_app
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator
from fastapi import FastAPI

# Create app WITHOUT the default lifespan (which connects to PostgreSQL)
async def _noop_lifespan(app: FastAPI) -> AsyncGenerator[None]:
    yield  # no startup/shutdown needed — we handle it in init_db()

# Build app manually to avoid the default PostgreSQL lifespan
from app.core.config import settings
from app.api.router import api_router

app = FastAPI(
    title=settings.project_name,
    version=settings.version,
    debug=settings.debug,
    lifespan=asynccontextmanager(_noop_lifespan),
)

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

# Override DB dependency to use SQLite
from app.db.session import get_db

async def _override_get_db():
    async with dev_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

app.dependency_overrides[get_db] = _override_get_db

# ── Create tables + seed data on startup ───────────────────────
STUB_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")

async def init_db():
    """Create all tables and seed initial data."""
    async with dev_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with dev_session_factory() as session:
        from sqlalchemy import text

        # Seed stub user
        result = await session.execute(
            text("SELECT 1 FROM users WHERE id = :uid"),
            {"uid": str(STUB_USER_ID)},
        )
        if result.scalar_one_or_none() is None:
            from app.models.user import User
            user = User(
                id=STUB_USER_ID,
                email="dev@forgemind.dev",
                display_name="Dev User",
            )
            session.add(user)
            await session.flush()

        # Seed default agents
        from app.services.agent_service import seed_default_agents
        try:
            await seed_default_agents(session)
        except Exception:
            await session.rollback()

        # Seed default connectors
        from app.services.connector_service import seed_default_connectors
        try:
            await seed_default_connectors(session)
        except Exception:
            await session.rollback()

        await session.commit()

    print("✓ Database initialized (SQLite: dev.db)")
    print("✓ Default agents and connectors seeded")


if __name__ == "__main__":
    import uvicorn

    # Initialize DB before starting server
    asyncio.run(init_db())

    print()
    print("=" * 56)
    print("  ForgeMind API — Dev Server (SQLite)")
    print("  http://localhost:8000")
    print("  Swagger: http://localhost:8000/docs")
    print("=" * 56)
    print()

    uvicorn.run(
        "dev_server:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info",
    )
