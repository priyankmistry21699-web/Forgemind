"""Human-style operator exercise for ForgeMind.

Drives the FastAPI app directly (via ASGITransport + aiosqlite, same setup the
test-suite uses) through a real operator scenario:

    1. create a project
    2. submit a prompt via /planner/intake
    3. inspect the generated plan/tasks/runs
    4. list artifacts + dashboard-level endpoints

This exists so a release can be validated end-to-end without standing up
docker-compose (Postgres/Redis/MinIO) on this workstation.
"""

from __future__ import annotations

import asyncio
import json
import sys
import tempfile
import uuid
from pathlib import Path

# Ensure apps/api is on sys.path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "apps" / "api"))

# Import the conftest-equivalent bootstrap (patches PG types for SQLite).
from sqlalchemy.dialects.postgresql import ARRAY, UUID as PG_UUID, JSON as PG_JSON
from sqlalchemy import Uuid, JSON
from sqlalchemy.ext.compiler import compiles


@compiles(ARRAY, "sqlite")
def _compile_array_sqlite(type_, compiler, **kw):  # type: ignore[no-redef]
    return "JSON"


from app.db.base_class import Base  # noqa: E402
from app.db.base import *  # noqa: E402, F401, F403


def _patch_metadata_for_sqlite() -> None:
    for table in Base.metadata.tables.values():
        for column in table.columns:
            if isinstance(column.type, PG_UUID):
                column.type = Uuid(as_uuid=True)
            elif isinstance(column.type, ARRAY):
                column.type = JSON()
            elif isinstance(column.type, PG_JSON):
                column.type = JSON()


_patch_metadata_for_sqlite()

from sqlalchemy import text  # noqa: E402
from sqlalchemy.ext.asyncio import (  # noqa: E402
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from httpx import AsyncClient, ASGITransport  # noqa: E402

from app.db.session import get_db  # noqa: E402
from app.main import create_app  # noqa: E402
from app.models.user import User  # noqa: E402


STUB_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


async def main() -> int:
    def _json_ser(v: object) -> str:
        return json.dumps(v, default=str)

    # File-backed SQLite so separate request-scoped sessions see the same data.
    tmp = tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False)
    tmp.close()
    db_path = Path(tmp.name)
    engine = create_async_engine(
        f"sqlite+aiosqlite:///{db_path.as_posix()}",
        echo=False,
        connect_args={"check_same_thread": False},
        json_serializer=_json_ser,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with session_factory() as seed:
        if (
            await seed.execute(
                text("SELECT 1 FROM users WHERE id = :u"),
                {"u": str(STUB_USER_ID)},
            )
        ).scalar_one_or_none() is None:
            seed.add(
                User(
                    id=STUB_USER_ID,
                    email="operator@forgemind.dev",
                    display_name="Operator",
                )
            )
            await seed.commit()

    app = create_app()

    async def _override() -> AsyncSession:
        async with session_factory() as s:
            yield s

    app.dependency_overrides[get_db] = _override

    transport = ASGITransport(app=app)
    results: dict[str, object] = {}

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Health
        r = await ac.get("/health")
        results["health"] = {"status": r.status_code, "body": r.json()}

        # 2. Create project
        r = await ac.post(
            "/projects",
            json={
                "name": "Operator Exercise — Task API",
                "description": "Build a small REST task API with FastAPI + SQLite",
            },
        )
        results["create_project"] = {"status": r.status_code}
        assert r.status_code == 201, r.text
        project = r.json()
        project_id = project["id"]
        results["create_project"]["project_id"] = project_id

        # 3. Prompt intake
        r = await ac.post(
            "/planner/intake",
            json={
                "project_id": project_id,
                "prompt": (
                    "Build a REST API for task management using FastAPI with "
                    "SQLite persistence. Include CRUD endpoints, simple "
                    "validation, and a small test suite."
                ),
            },
        )
        results["prompt_intake"] = {
            "status": r.status_code,
            "keys": sorted(r.json().keys()) if r.status_code < 500 else None,
        }

        intake_body = r.json() if r.status_code < 500 else {}

        # 4. List runs + tasks for the project
        r = await ac.get(f"/projects/{project_id}/runs?skip=0&limit=20")
        results["runs_list"] = {
            "status": r.status_code,
            "total": r.json().get("total") if r.status_code == 200 else None,
        }

        runs = r.json().get("items", []) if r.status_code == 200 else []
        if runs:
            run_id = runs[0]["id"]
            r = await ac.get(f"/runs/{run_id}")
            results["run_detail"] = {"status": r.status_code}

            r = await ac.get(f"/projects/{project_id}/artifacts?run_id={run_id}")
            results["artifacts_for_run"] = {
                "status": r.status_code,
                "total": r.json().get("total")
                if r.status_code == 200
                else None,
            }

        # 5. Approvals surface for the project
        r = await ac.get(f"/approvals?project_id={project_id}")
        results["approvals"] = {
            "status": r.status_code,
            "total": r.json().get("total") if r.status_code == 200 else None,
        }

        # 6. Project detail read-back
        r = await ac.get(f"/projects/{project_id}")
        results["project_detail"] = {"status": r.status_code}

        # 7. Events surface
        r = await ac.get(f"/events?project_id={project_id}&limit=50")
        results["events"] = {
            "status": r.status_code,
            "total": r.json().get("total") if r.status_code == 200 else None,
        }

        # 8. Intake plan summary (if present)
        plan_summary = None
        if isinstance(intake_body, dict):
            plan = intake_body.get("plan") or intake_body.get("planner_result")
            if isinstance(plan, dict):
                plan_summary = {
                    "task_count": len(
                        plan.get("tasks") or plan.get("items") or []
                    ),
                    "keys": sorted(plan.keys()),
                }
        results["plan_summary"] = plan_summary

    app.dependency_overrides.clear()
    await engine.dispose()
    try:
        db_path.unlink()
    except OSError:
        pass

    print(json.dumps(results, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
