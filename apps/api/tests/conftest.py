"""
Shared test fixtures for ForgeMind API tests.

Uses an in-memory SQLite database via aiosqlite so tests run without
any external infrastructure (no Docker / PostgreSQL required).
"""

import asyncio
import uuid
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy import event, text

from app.db.base_class import Base

# ── Patch PostgreSQL types for SQLite compatibility ──────────────
# Must happen BEFORE models are imported so the compiler is registered.
from sqlalchemy.dialects.postgresql import ARRAY, UUID as PG_UUID, JSON as PG_JSON
from sqlalchemy import Uuid, JSON, String
from sqlalchemy.ext.compiler import compiles

@compiles(ARRAY, "sqlite")
def _compile_array_sqlite(type_, compiler, **kw):
    return "JSON"

# Import all models so metadata is populated
from app.db.base import *  # noqa: F401, F403


def _patch_metadata_for_sqlite():
    """Replace PostgreSQL-specific column types with SQLite-compatible ones."""
    for table in Base.metadata.tables.values():
        for column in table.columns:
            if isinstance(column.type, PG_UUID):
                column.type = Uuid(as_uuid=True)
            elif isinstance(column.type, ARRAY):
                column.type = JSON()
            elif isinstance(column.type, PG_JSON):
                column.type = JSON()


_patch_metadata_for_sqlite()

# ── SQLite in-memory URL ─────────────────────────────────────────
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# ── Stub user for auth ───────────────────────────────────────────
STUB_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


# ── Event loop ───────────────────────────────────────────────────
@pytest.fixture(scope="session")
def event_loop():
    """Create a single event loop for the entire test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ── Test engine (session-scoped, shared across all tests) ────────
@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Async engine backed by in-memory SQLite."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False},
    )
    # Create all tables once
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Provide a database session that truncates all tables after each test."""
    session_factory = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        yield session
        await session.rollback()
        # Clean all tables after each test for isolation
        async with test_engine.begin() as conn:
            for table in reversed(Base.metadata.sorted_tables):
                await conn.execute(table.delete())


# ── Seed stub user ───────────────────────────────────────────────
@pytest_asyncio.fixture(autouse=True)
async def seed_stub_user(db_session: AsyncSession):
    """Ensure the stub user exists for auth_stub dependency."""
    from app.models.user import User

    result = await db_session.execute(
        text("SELECT 1 FROM users WHERE id = :uid"),
        {"uid": str(STUB_USER_ID)},
    )
    if result.scalar_one_or_none() is None:
        user = User(
            id=STUB_USER_ID,
            email="test@forgemind.dev",
            display_name="Test User",
        )
        db_session.add(user)
        await db_session.commit()


# ── FastAPI test client ──────────────────────────────────────────
@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client wired to the FastAPI app with test DB override."""
    from app.db.session import get_db
    from app.main import create_app

    app = create_app()

    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


# ── Test data factories ──────────────────────────────────────────
@pytest_asyncio.fixture
async def sample_project(db_session: AsyncSession):
    """Create and return a sample project for tests."""
    from app.models.project import Project

    project = Project(
        name="Test Project",
        description="A project for testing",
        owner_id=STUB_USER_ID,
    )
    db_session.add(project)
    await db_session.flush()
    await db_session.refresh(project)
    return project


@pytest_asyncio.fixture
async def sample_run(db_session: AsyncSession, sample_project):
    """Create and return a sample run linked to the sample project."""
    from app.models.run import Run

    run = Run(
        run_number=1,
        project_id=sample_project.id,
        trigger="test",
    )
    db_session.add(run)
    await db_session.flush()
    await db_session.refresh(run)
    return run


@pytest_asyncio.fixture
async def sample_task(db_session: AsyncSession, sample_run):
    """Create and return a sample READY task linked to the sample run."""
    from app.models.task import Task, TaskStatus

    task = Task(
        title="Test Task",
        description="A task for testing",
        task_type="architecture",
        status=TaskStatus.READY,
        order_index=0,
        run_id=sample_run.id,
    )
    db_session.add(task)
    await db_session.flush()
    await db_session.refresh(task)
    return task


@pytest_asyncio.fixture
async def sample_artifact(db_session: AsyncSession, sample_project, sample_run, sample_task):
    """Create and return a sample artifact."""
    from app.models.artifact import Artifact, ArtifactType

    artifact = Artifact(
        title="Test Artifact",
        artifact_type=ArtifactType.ARCHITECTURE,
        content="# Architecture\nTest content",
        project_id=sample_project.id,
        run_id=sample_run.id,
        task_id=sample_task.id,
        created_by="test-agent",
    )
    db_session.add(artifact)
    await db_session.flush()
    await db_session.refresh(artifact)
    return artifact


@pytest_asyncio.fixture
async def sample_approval(db_session: AsyncSession, sample_project, sample_run, sample_task):
    """Create and return a pending approval request."""
    from app.models.approval_request import ApprovalRequest, ApprovalStatus

    approval = ApprovalRequest(
        title="Approve architecture",
        description="Review the architecture artifact before proceeding.",
        status=ApprovalStatus.PENDING,
        project_id=sample_project.id,
        run_id=sample_run.id,
        task_id=sample_task.id,
    )
    db_session.add(approval)
    await db_session.flush()
    await db_session.refresh(approval)
    return approval


@pytest_asyncio.fixture
async def sample_planner_result(db_session: AsyncSession, sample_run):
    """Create and return a planner result for tests."""
    from app.models.planner_result import PlannerResult

    pr = PlannerResult(
        run_id=sample_run.id,
        overview="Test planner overview — build an API",
        recommended_stack={"language": "Python", "framework": "FastAPI", "database": "PostgreSQL"},
        assumptions=["Users have Python 3.12+", "PostgreSQL is available"],
        next_steps=["Set up project", "Build API endpoints"],
    )
    db_session.add(pr)
    await db_session.flush()
    await db_session.refresh(pr)
    return pr
