"""
Local dev server using SQLite — no Docker or PostgreSQL required.

Usage:
    cd apps/api
    python run_dev_sqlite.py

Starts the ForgeMind API on http://localhost:8000 with a file-based SQLite DB.
"""

import asyncio
import os

# ── 1. Force SQLite DATABASE_URL before anything imports settings ──
DB_PATH = os.path.join(os.path.dirname(__file__), "forgemind_dev.db")
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{DB_PATH}"

# ── 2. Patch PostgreSQL column types for SQLite compatibility ──
from sqlalchemy.dialects.postgresql import ARRAY, UUID as PG_UUID, JSON as PG_JSON
from sqlalchemy import Uuid, JSON
from sqlalchemy.ext.compiler import compiles


@compiles(ARRAY, "sqlite")
def _compile_array_sqlite(type_, compiler, **kw):
    return "JSON"


# Import models so metadata is populated
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

# ── 3. Re-create engine with SQLite-compatible settings ──
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
import app.db.session as db_session_mod

engine = create_async_engine(
    f"sqlite+aiosqlite:///{DB_PATH}",
    echo=False,
    connect_args={"check_same_thread": False},
)
session_factory = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# Monkey-patch the session module so the app uses our SQLite engine
db_session_mod.engine = engine
db_session_mod.async_session_factory = session_factory


async def init_db():
    """Create all tables and seed data."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print(f"[dev] SQLite database ready at {DB_PATH}")


async def seed_demo_data():
    """Seed a demo user and project for UI exploration."""
    import uuid
    from app.models.user import User
    from app.models.project import Project
    from sqlalchemy import text

    DEMO_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")

    async with session_factory() as session:
        # Check if demo user exists
        result = await session.execute(
            text("SELECT 1 FROM users WHERE id = :uid"),
            {"uid": str(DEMO_USER_ID)},
        )
        if result.scalar_one_or_none() is None:
            user = User(
                id=DEMO_USER_ID,
                email="demo@forgemind.dev",
                display_name="Demo User",
            )
            session.add(user)
            await session.commit()
            print("[dev] Seeded demo user: demo@forgemind.dev")

        # Check if demo project exists
        result = await session.execute(
            text("SELECT 1 FROM projects WHERE name = :name"),
            {"name": "Demo Project"},
        )
        if result.scalar_one_or_none() is None:
            project = Project(
                name="Demo Project",
                description="A demo project for exploring the ForgeMind UI.",
                owner_id=DEMO_USER_ID,
            )
            session.add(project)
            await session.commit()
            print("[dev] Seeded demo project: 'Demo Project'")


if __name__ == "__main__":
    # Initialize DB
    asyncio.run(init_db())
    asyncio.run(seed_demo_data())

    # Start server
    import uvicorn
    from app.main import create_app

    app = create_app()
    print("\n[dev] ForgeMind API starting on http://localhost:8000")
    print("[dev] Swagger docs: http://localhost:8000/docs")
    print("[dev] Using SQLite (no Docker required)\n")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
