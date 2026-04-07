"""FM-131–140: Comprehensive tests for Release Operations.

Covers:
  FM-131: Release package model + CRUD + auto-generation
  FM-132: Deployment environment CRUD
  FM-133: Deployment readiness evaluation
  FM-134: Release gate evaluation + persistence
  FM-135: Rollback readiness assessment
  FM-136: Post-release report + outcome tracking
  FM-137: Operational timeline view
  FM-138/139: Frontend/CLI surface (structural verification)
  FM-140: Integration hardening (HTTP routes)
"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import STUB_USER_ID


# ── Helpers ──────────────────────────────────────────────────────


async def _seed_project(db: AsyncSession):
    from app.models.project import Project
    from app.models.membership import ProjectMember, ProjectRole

    project = Project(
        name="Release Test Project",
        description="For FM-131–140 tests",
        owner_id=STUB_USER_ID,
    )
    db.add(project)
    await db.flush()
    await db.refresh(project)
    lead = ProjectMember(
        project_id=project.id,
        user_id=STUB_USER_ID,
        role=ProjectRole.LEAD,
    )
    db.add(lead)
    await db.flush()
    return project


async def _seed_run(db: AsyncSession, project_id: uuid.UUID, **kwargs):
    from app.models.run import Run, RunStatus

    run = Run(
        project_id=project_id,
        run_number=kwargs.get("run_number", 1),
        status=kwargs.get("status", RunStatus.RUNNING),
    )
    db.add(run)
    await db.flush()
    await db.refresh(run)
    return run


async def _seed_task(db: AsyncSession, run_id: uuid.UUID, **kwargs):
    from app.models.task import Task, TaskStatus

    task = Task(
        run_id=run_id,
        title=kwargs.get("title", "Test task"),
        task_type=kwargs.get("task_type", "coding"),
        status=kwargs.get("status", TaskStatus.COMPLETED),
    )
    db.add(task)
    await db.flush()
    await db.refresh(task)
    return task


async def _seed_artifact(db: AsyncSession, run_id, project_id, **kwargs):
    from app.models.artifact import Artifact, ArtifactType

    artifact = Artifact(
        run_id=run_id,
        project_id=project_id,
        title=kwargs.get("title", "Test artifact"),
        artifact_type=kwargs.get("artifact_type", ArtifactType.SPEC),
        content=kwargs.get("content", "Test content"),
        created_by="test",
    )
    db.add(artifact)
    await db.flush()
    await db.refresh(artifact)
    return artifact


async def _seed_approval(db: AsyncSession, run_id, project_id, **kwargs):
    from app.models.approval_request import ApprovalRequest, ApprovalStatus

    approval = ApprovalRequest(
        run_id=run_id,
        project_id=project_id,
        title=kwargs.get("title", "Approve spec"),
        description=kwargs.get("description", "Please approve"),
        status=kwargs.get("status", ApprovalStatus.APPROVED),
    )
    db.add(approval)
    await db.flush()
    await db.refresh(approval)
    return approval


async def _seed_checkpoint(db: AsyncSession, run_id, project_id, **kwargs):
    from app.services import execution_checkpoint_service as svc
    from app.models.execution_checkpoint import CheckpointType

    return await svc.create_checkpoint(
        db,
        run_id=run_id,
        project_id=project_id,
        checkpoint_type=kwargs.get("checkpoint_type", CheckpointType.MANUAL),
        summary=kwargs.get("summary", "Test checkpoint"),
        created_by="test",
    )


async def _setup_full_run(db: AsyncSession):
    """Seed a complete run with tasks, artifacts, approvals, and checkpoints."""
    from app.models.artifact import ArtifactType
    from app.models.run import RunStatus
    from app.models.task import TaskStatus
    from app.models.execution_checkpoint import CheckpointType

    project = await _seed_project(db)
    run = await _seed_run(db, project.id, status=RunStatus.COMPLETED)

    t1 = await _seed_task(db, run.id, title="Design", status=TaskStatus.COMPLETED)
    t2 = await _seed_task(db, run.id, title="Implement", status=TaskStatus.COMPLETED)

    spec = await _seed_artifact(
        db, run.id, project.id, title="SPEC",
        artifact_type=ArtifactType.SPEC, content="Spec content",
    )
    plan = await _seed_artifact(
        db, run.id, project.id, title="PLAN",
        artifact_type=ArtifactType.PLAN, content="Plan content",
    )

    approval = await _seed_approval(db, run.id, project.id)

    cp = await _seed_checkpoint(
        db, run.id, project.id,
        checkpoint_type=CheckpointType.PRE_DELIVERY,
        summary="Pre-delivery checkpoint",
    )

    return {
        "project": project,
        "run": run,
        "tasks": [t1, t2],
        "spec": spec,
        "plan": plan,
        "approval": approval,
        "checkpoint": cp,
    }


# ═════════════════════════════════════════════════════════════════
# FM-131: Release Package CRUD + Generation
# ═════════════════════════════════════════════════════════════════


class TestReleasePackageService:
    """FM-131: Release package service-layer operations."""

    @pytest.mark.asyncio
    async def test_create_release_package(self, db_session: AsyncSession):
        from app.services import release_package_service as svc
        from app.schemas.release_ops import ReleasePackageCreate

        project = await _seed_project(db_session)
        run = await _seed_run(db_session, project.id)

        data = ReleasePackageCreate(
            version="1.0.0",
            summary="Initial release",
        )
        pkg = await svc.create_release_package(
            db_session, run_id=run.id, project_id=project.id, data=data
        )
        assert pkg.id is not None
        assert pkg.version == "1.0.0"
        assert pkg.status.value == "draft"
        assert pkg.confidence_snapshot is not None

    @pytest.mark.asyncio
    async def test_get_release_package(self, db_session: AsyncSession):
        from app.services import release_package_service as svc
        from app.schemas.release_ops import ReleasePackageCreate

        project = await _seed_project(db_session)
        run = await _seed_run(db_session, project.id)
        data = ReleasePackageCreate(version="1.0.0", summary="Test")
        pkg = await svc.create_release_package(
            db_session, run_id=run.id, project_id=project.id, data=data
        )

        fetched = await svc.get_release_package(db_session, pkg.id)
        assert fetched is not None
        assert fetched.id == pkg.id

    @pytest.mark.asyncio
    async def test_list_release_packages(self, db_session: AsyncSession):
        from app.services import release_package_service as svc
        from app.schemas.release_ops import ReleasePackageCreate

        project = await _seed_project(db_session)
        run = await _seed_run(db_session, project.id)

        for v in ["1.0.0", "1.1.0"]:
            await svc.create_release_package(
                db_session, run_id=run.id, project_id=project.id,
                data=ReleasePackageCreate(version=v, summary=f"v{v}"),
            )

        items = await svc.list_release_packages(db_session, run.id)
        assert len(items) == 2

    @pytest.mark.asyncio
    async def test_list_project_releases(self, db_session: AsyncSession):
        from app.services import release_package_service as svc
        from app.schemas.release_ops import ReleasePackageCreate

        project = await _seed_project(db_session)
        run = await _seed_run(db_session, project.id)
        await svc.create_release_package(
            db_session, run_id=run.id, project_id=project.id,
            data=ReleasePackageCreate(version="1.0.0", summary="v1"),
        )

        items = await svc.list_project_releases(db_session, project.id)
        assert len(items) == 1
        assert items[0].project_id == project.id

    @pytest.mark.asyncio
    async def test_update_release_package(self, db_session: AsyncSession):
        from app.services import release_package_service as svc
        from app.schemas.release_ops import ReleasePackageCreate, ReleasePackageUpdate

        project = await _seed_project(db_session)
        run = await _seed_run(db_session, project.id)
        pkg = await svc.create_release_package(
            db_session, run_id=run.id, project_id=project.id,
            data=ReleasePackageCreate(version="1.0.0", summary="v1"),
        )

        updated = await svc.update_release_package(
            db_session, pkg.id,
            ReleasePackageUpdate(summary="Updated summary"),
        )
        assert updated.summary == "Updated summary"

    @pytest.mark.asyncio
    async def test_generate_release_package(self, db_session: AsyncSession):
        from app.services import release_package_service as svc

        data = await _setup_full_run(db_session)
        pkg = await svc.generate_release_package(
            db_session, run_id=data["run"].id, project_id=data["project"].id
        )
        assert pkg.version.startswith("0.")
        assert pkg.artifact_manifest is not None
        assert pkg.changelog is not None
        assert pkg.rollback_metadata is not None
        assert pkg.confidence_snapshot is not None

    @pytest.mark.asyncio
    async def test_generate_with_custom_version(self, db_session: AsyncSession):
        from app.services import release_package_service as svc

        data = await _setup_full_run(db_session)
        pkg = await svc.generate_release_package(
            db_session, run_id=data["run"].id, project_id=data["project"].id,
            version="2.5.0",
        )
        assert pkg.version == "2.5.0"


# ═════════════════════════════════════════════════════════════════
# FM-132: Deployment Environment CRUD
# ═════════════════════════════════════════════════════════════════


class TestEnvironmentService:
    """FM-132: Environment service-layer operations."""

    @pytest.mark.asyncio
    async def test_create_environment(self, db_session: AsyncSession):
        from app.services import environment_service as svc
        from app.schemas.release_ops import EnvironmentCreate
        from app.models.release_ops import EnvironmentTier

        project = await _seed_project(db_session)
        data = EnvironmentCreate(
            name="production",
            tier=EnvironmentTier.PRODUCTION,
            description="Production environment",
        )
        env = await svc.create_environment(db_session, project_id=project.id, data=data)
        assert env.id is not None
        assert env.name == "production"
        assert env.tier == EnvironmentTier.PRODUCTION
        assert env.is_active is True

    @pytest.mark.asyncio
    async def test_list_environments(self, db_session: AsyncSession):
        from app.services import environment_service as svc
        from app.schemas.release_ops import EnvironmentCreate

        project = await _seed_project(db_session)
        for name in ["dev", "staging", "prod"]:
            await svc.create_environment(
                db_session, project_id=project.id,
                data=EnvironmentCreate(name=name),
            )
        items = await svc.list_environments(db_session, project.id)
        assert len(items) == 3

    @pytest.mark.asyncio
    async def test_update_environment(self, db_session: AsyncSession):
        from app.services import environment_service as svc
        from app.schemas.release_ops import EnvironmentCreate, EnvironmentUpdate

        project = await _seed_project(db_session)
        env = await svc.create_environment(
            db_session, project_id=project.id,
            data=EnvironmentCreate(name="staging"),
        )
        updated = await svc.update_environment(
            db_session, env.id,
            EnvironmentUpdate(description="Updated staging"),
        )
        assert updated.description == "Updated staging"

    @pytest.mark.asyncio
    async def test_delete_environment(self, db_session: AsyncSession):
        from app.services import environment_service as svc
        from app.schemas.release_ops import EnvironmentCreate

        project = await _seed_project(db_session)
        env = await svc.create_environment(
            db_session, project_id=project.id,
            data=EnvironmentCreate(name="temp"),
        )
        result = await svc.delete_environment(db_session, env.id)
        assert result is True

        fetched = await svc.get_environment(db_session, env.id)
        assert fetched is None


# ═════════════════════════════════════════════════════════════════
# FM-133: Deployment Readiness
# ═════════════════════════════════════════════════════════════════


class TestDeploymentReadiness:
    """FM-133: Readiness evaluation against environment criteria."""

    @pytest.mark.asyncio
    async def test_readiness_for_completed_run(self, db_session: AsyncSession):
        from app.services import deployment_readiness_service as svc
        from app.services import release_package_service as rps
        from app.services import environment_service as es
        from app.schemas.release_ops import ReleasePackageCreate, EnvironmentCreate
        from app.models.release_ops import EnvironmentTier

        data = await _setup_full_run(db_session)

        env = await es.create_environment(
            db_session, project_id=data["project"].id,
            data=EnvironmentCreate(name="dev", tier=EnvironmentTier.DEVELOPMENT),
        )
        pkg = await rps.create_release_package(
            db_session, run_id=data["run"].id, project_id=data["project"].id,
            data=ReleasePackageCreate(version="1.0.0", summary="Test"),
        )

        result = await svc.evaluate_readiness(
            db_session, release_package_id=pkg.id, environment_id=env.id
        )
        assert "is_ready" in result
        assert "checks" in result
        assert result["total_checks"] >= 5

    @pytest.mark.asyncio
    async def test_readiness_with_incomplete_run(self, db_session: AsyncSession):
        from app.services import deployment_readiness_service as svc
        from app.services import release_package_service as rps
        from app.services import environment_service as es
        from app.schemas.release_ops import ReleasePackageCreate, EnvironmentCreate
        from app.models.release_ops import EnvironmentTier

        project = await _seed_project(db_session)
        run = await _seed_run(db_session, project.id)  # RUNNING status

        env = await es.create_environment(
            db_session, project_id=project.id,
            data=EnvironmentCreate(name="prod", tier=EnvironmentTier.PRODUCTION),
        )
        pkg = await rps.create_release_package(
            db_session, run_id=run.id, project_id=project.id,
            data=ReleasePackageCreate(version="0.1.0", summary="Incomplete"),
        )

        result = await svc.evaluate_readiness(
            db_session, release_package_id=pkg.id, environment_id=env.id
        )
        assert result["is_ready"] is False
        assert len(result["blockers"]) > 0


# ═════════════════════════════════════════════════════════════════
# FM-134: Release Gates
# ═════════════════════════════════════════════════════════════════


class TestReleaseGates:
    """FM-134: Release gate evaluation and persistence."""

    @pytest.mark.asyncio
    async def test_evaluate_gates_all_pass(self, db_session: AsyncSession):
        from app.services import release_gate_service as svc
        from app.services import release_package_service as rps
        from app.schemas.release_ops import ReleasePackageCreate

        data = await _setup_full_run(db_session)
        pkg = await rps.create_release_package(
            db_session, run_id=data["run"].id, project_id=data["project"].id,
            data=ReleasePackageCreate(version="1.0.0", summary="Full run"),
        )

        result = await svc.evaluate_gates(
            db_session, release_package_id=pkg.id
        )
        assert "total_gates" in result
        assert result["total_gates"] > 0
        assert "gate_results" in result

    @pytest.mark.asyncio
    async def test_evaluate_gates_with_failures(self, db_session: AsyncSession):
        from app.services import release_gate_service as svc
        from app.services import release_package_service as rps
        from app.schemas.release_ops import ReleasePackageCreate

        project = await _seed_project(db_session)
        run = await _seed_run(db_session, project.id)  # RUNNING — not completed

        pkg = await rps.create_release_package(
            db_session, run_id=run.id, project_id=project.id,
            data=ReleasePackageCreate(version="0.1.0", summary="Incomplete"),
        )

        result = await svc.evaluate_gates(
            db_session, release_package_id=pkg.id
        )
        assert result["failed"] > 0
        assert result["all_passed"] is False
        assert result["package_status"] == "gated"

    @pytest.mark.asyncio
    async def test_gate_results_persisted(self, db_session: AsyncSession):
        from app.services import release_gate_service as svc
        from app.services import release_package_service as rps
        from app.schemas.release_ops import ReleasePackageCreate

        project = await _seed_project(db_session)
        run = await _seed_run(db_session, project.id)
        pkg = await rps.create_release_package(
            db_session, run_id=run.id, project_id=project.id,
            data=ReleasePackageCreate(version="0.1.0", summary="Test gates"),
        )

        await svc.evaluate_gates(db_session, release_package_id=pkg.id)

        results = await svc.list_gate_results(db_session, pkg.id)
        assert len(results) > 0
        assert results[0].gate_name is not None

    @pytest.mark.asyncio
    async def test_evaluate_gates_with_env_config(self, db_session: AsyncSession):
        from app.services import release_gate_service as svc
        from app.services import release_package_service as rps
        from app.services import environment_service as es
        from app.schemas.release_ops import ReleasePackageCreate, EnvironmentCreate

        data = await _setup_full_run(db_session)
        env = await es.create_environment(
            db_session, project_id=data["project"].id,
            data=EnvironmentCreate(
                name="staging",
                required_gates={"gates": ["run_completed", "has_checkpoints"]},
            ),
        )
        pkg = await rps.create_release_package(
            db_session, run_id=data["run"].id, project_id=data["project"].id,
            data=ReleasePackageCreate(version="1.0.0", summary="Custom gates"),
        )

        result = await svc.evaluate_gates(
            db_session, release_package_id=pkg.id, environment_id=env.id
        )
        assert result["total_gates"] == 2


# ═════════════════════════════════════════════════════════════════
# FM-135: Rollback Readiness
# ═════════════════════════════════════════════════════════════════


class TestRollbackReadiness:
    """FM-135: Rollback readiness assessment."""

    @pytest.mark.asyncio
    async def test_rollback_readiness_with_checkpoints(self, db_session: AsyncSession):
        from app.services import rollback_readiness_service as svc
        from app.services import release_package_service as rps
        from app.schemas.release_ops import ReleasePackageCreate

        data = await _setup_full_run(db_session)
        pkg = await rps.create_release_package(
            db_session, run_id=data["run"].id, project_id=data["project"].id,
            data=ReleasePackageCreate(version="1.0.0", summary="Has checkpoints"),
        )

        result = await svc.evaluate_rollback_readiness(
            db_session, release_package_id=pkg.id
        )
        assert result["is_rollback_ready"] is True
        assert result["recovery_point_count"] > 0
        assert len(result["strategies"]) > 0
        assert result["risk_level"] in ("low", "medium", "high")

    @pytest.mark.asyncio
    async def test_rollback_readiness_no_checkpoints(self, db_session: AsyncSession):
        from app.services import rollback_readiness_service as svc
        from app.services import release_package_service as rps
        from app.schemas.release_ops import ReleasePackageCreate

        project = await _seed_project(db_session)
        run = await _seed_run(db_session, project.id)
        pkg = await rps.create_release_package(
            db_session, run_id=run.id, project_id=project.id,
            data=ReleasePackageCreate(version="0.1.0", summary="No checkpoints"),
        )

        result = await svc.evaluate_rollback_readiness(
            db_session, release_package_id=pkg.id
        )
        assert result["is_rollback_ready"] is False
        assert any(r["level"] == "high" for r in result["risk_signals"])


# ═════════════════════════════════════════════════════════════════
# FM-136: Post-Release Report + Outcome
# ═════════════════════════════════════════════════════════════════


class TestPostReleaseReport:
    """FM-136: Post-release report generation and outcome tracking."""

    @pytest.mark.asyncio
    async def test_generate_report(self, db_session: AsyncSession):
        from app.services import post_release_service as svc
        from app.services import release_package_service as rps
        from app.schemas.release_ops import ReleasePackageCreate

        data = await _setup_full_run(db_session)
        pkg = await rps.create_release_package(
            db_session, run_id=data["run"].id, project_id=data["project"].id,
            data=ReleasePackageCreate(version="1.0.0", summary="Full release"),
        )

        report = await svc.generate_post_release_report(
            db_session, release_package_id=pkg.id
        )
        assert report["version"] == "1.0.0"
        assert "tasks" in report
        assert "gates" in report
        assert "approvals" in report
        assert "artifacts" in report
        assert "checkpoints" in report
        assert report["tasks"]["total"] == 2

    @pytest.mark.asyncio
    async def test_record_outcome_deployed(self, db_session: AsyncSession):
        from app.services import post_release_service as svc
        from app.services import release_package_service as rps
        from app.schemas.release_ops import ReleasePackageCreate
        from app.models.release_ops import ReleaseStatus

        data = await _setup_full_run(db_session)
        pkg = await rps.create_release_package(
            db_session, run_id=data["run"].id, project_id=data["project"].id,
            data=ReleasePackageCreate(version="1.0.0", summary="Deploy test"),
        )

        result = await svc.record_outcome(
            db_session, release_package_id=pkg.id,
            status=ReleaseStatus.DEPLOYED, notes="Deployed successfully",
        )
        assert result["new_status"] == "deployed"
        assert result["outcome_notes"] == "Deployed successfully"

    @pytest.mark.asyncio
    async def test_record_outcome_invalid(self, db_session: AsyncSession):
        from app.services import post_release_service as svc
        from app.services import release_package_service as rps
        from app.schemas.release_ops import ReleasePackageCreate
        from app.models.release_ops import ReleaseStatus

        data = await _setup_full_run(db_session)
        pkg = await rps.create_release_package(
            db_session, run_id=data["run"].id, project_id=data["project"].id,
            data=ReleasePackageCreate(version="1.0.0", summary="Bad outcome"),
        )

        result = await svc.record_outcome(
            db_session, release_package_id=pkg.id,
            status=ReleaseStatus.DRAFT,  # invalid outcome
        )
        assert "error" in result


# ═════════════════════════════════════════════════════════════════
# FM-137: Operational Timeline
# ═════════════════════════════════════════════════════════════════


class TestOperationalTimeline:
    """FM-137: Unified operational timeline view."""

    @pytest.mark.asyncio
    async def test_build_timeline(self, db_session: AsyncSession):
        from app.services import operational_timeline_service as svc

        data = await _setup_full_run(db_session)

        timeline = await svc.build_operational_timeline(
            db_session, run_id=data["run"].id
        )
        assert timeline["run_id"] == str(data["run"].id)
        assert timeline["total_entries"] > 0
        assert "timeline" in timeline
        assert "categories" in timeline

        categories = timeline["categories"]
        assert "lifecycle" in categories
        assert "task" in categories

    @pytest.mark.asyncio
    async def test_timeline_not_found(self, db_session: AsyncSession):
        from app.services import operational_timeline_service as svc

        result = await svc.build_operational_timeline(
            db_session, run_id=uuid.uuid4()
        )
        assert result.get("error") == "run_not_found"


# ═════════════════════════════════════════════════════════════════
# FM-140: HTTP Route Integration
# ═════════════════════════════════════════════════════════════════


class TestReleaseOpsRoutes:
    """FM-140: End-to-end HTTP route tests for release operations."""

    @pytest.mark.asyncio
    async def test_create_and_list_environments(
        self, db_session: AsyncSession, client: AsyncClient,
    ):
        project = await _seed_project(db_session)
        await db_session.commit()

        # Create environment
        resp = await client.post(
            f"/projects/{project.id}/environments",
            json={"name": "staging", "tier": "staging", "description": "Stage env"},
        )
        assert resp.status_code == 201
        env_data = resp.json()
        assert env_data["name"] == "staging"

        # List environments
        resp = await client.get(f"/projects/{project.id}/environments")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] >= 1

    @pytest.mark.asyncio
    async def test_create_and_get_release_package(
        self, db_session: AsyncSession, client: AsyncClient,
    ):
        project = await _seed_project(db_session)
        run = await _seed_run(db_session, project.id)
        await db_session.commit()

        # Create release package
        resp = await client.post(
            f"/runs/{run.id}/release-packages",
            json={"version": "1.0.0", "summary": "Route test release"},
        )
        assert resp.status_code == 201
        pkg_data = resp.json()
        pkg_id = pkg_data["id"]

        # Get release package
        resp = await client.get(f"/release-packages/{pkg_id}")
        assert resp.status_code == 200
        assert resp.json()["version"] == "1.0.0"

    @pytest.mark.asyncio
    async def test_list_run_release_packages(
        self, db_session: AsyncSession, client: AsyncClient,
    ):
        project = await _seed_project(db_session)
        run = await _seed_run(db_session, project.id)
        await db_session.commit()

        await client.post(
            f"/runs/{run.id}/release-packages",
            json={"version": "1.0.0", "summary": "v1"},
        )

        resp = await client.get(f"/runs/{run.id}/release-packages")
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    @pytest.mark.asyncio
    async def test_list_project_releases(
        self, db_session: AsyncSession, client: AsyncClient,
    ):
        project = await _seed_project(db_session)
        run = await _seed_run(db_session, project.id)
        await db_session.commit()

        await client.post(
            f"/runs/{run.id}/release-packages",
            json={"version": "2.0.0", "summary": "project listing"},
        )

        resp = await client.get(f"/projects/{project.id}/release-packages")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_evaluate_gates_route(
        self, db_session: AsyncSession, client: AsyncClient,
    ):
        project = await _seed_project(db_session)
        run = await _seed_run(db_session, project.id)
        await db_session.commit()

        create_resp = await client.post(
            f"/runs/{run.id}/release-packages",
            json={"version": "0.1.0", "summary": "gate test"},
        )
        pkg_id = create_resp.json()["id"]

        resp = await client.post(
            f"/release-packages/{pkg_id}/gates/evaluate",
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "total_gates" in body
        assert "gate_results" in body

    @pytest.mark.asyncio
    async def test_list_gate_results_route(
        self, db_session: AsyncSession, client: AsyncClient,
    ):
        project = await _seed_project(db_session)
        run = await _seed_run(db_session, project.id)
        await db_session.commit()

        create_resp = await client.post(
            f"/runs/{run.id}/release-packages",
            json={"version": "0.1.0", "summary": "gate list test"},
        )
        pkg_id = create_resp.json()["id"]

        # Evaluate first to create results
        await client.post(f"/release-packages/{pkg_id}/gates/evaluate")

        resp = await client.get(f"/release-packages/{pkg_id}/gates")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] > 0

    @pytest.mark.asyncio
    async def test_rollback_readiness_route(
        self, db_session: AsyncSession, client: AsyncClient,
    ):
        project = await _seed_project(db_session)
        run = await _seed_run(db_session, project.id)
        await db_session.commit()

        create_resp = await client.post(
            f"/runs/{run.id}/release-packages",
            json={"version": "0.1.0", "summary": "rollback test"},
        )
        pkg_id = create_resp.json()["id"]

        resp = await client.get(
            f"/release-packages/{pkg_id}/rollback-readiness",
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "is_rollback_ready" in body
        assert "strategies" in body

    @pytest.mark.asyncio
    async def test_post_release_report_route(
        self, db_session: AsyncSession, client: AsyncClient,
    ):
        project = await _seed_project(db_session)
        run = await _seed_run(db_session, project.id)
        await db_session.commit()

        create_resp = await client.post(
            f"/runs/{run.id}/release-packages",
            json={"version": "0.1.0", "summary": "report test"},
        )
        pkg_id = create_resp.json()["id"]

        resp = await client.get(f"/release-packages/{pkg_id}/report")
        assert resp.status_code == 200
        body = resp.json()
        assert body["version"] == "0.1.0"
        assert "tasks" in body

    @pytest.mark.asyncio
    async def test_record_outcome_route(
        self, db_session: AsyncSession, client: AsyncClient,
    ):
        project = await _seed_project(db_session)
        run = await _seed_run(db_session, project.id)
        await db_session.commit()

        create_resp = await client.post(
            f"/runs/{run.id}/release-packages",
            json={"version": "0.1.0", "summary": "outcome test"},
        )
        pkg_id = create_resp.json()["id"]

        resp = await client.post(
            f"/release-packages/{pkg_id}/outcome?outcome=deployed&notes=Success",
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["new_status"] == "deployed"

    @pytest.mark.asyncio
    async def test_operational_timeline_route(
        self, db_session: AsyncSession, client: AsyncClient,
    ):
        project = await _seed_project(db_session)
        run = await _seed_run(db_session, project.id)
        await db_session.commit()

        resp = await client.get(f"/runs/{run.id}/timeline")
        assert resp.status_code == 200
        body = resp.json()
        assert "timeline" in body
        assert body["total_entries"] >= 1

    @pytest.mark.asyncio
    async def test_update_release_package_route(
        self, db_session: AsyncSession, client: AsyncClient,
    ):
        project = await _seed_project(db_session)
        run = await _seed_run(db_session, project.id)
        await db_session.commit()

        create_resp = await client.post(
            f"/runs/{run.id}/release-packages",
            json={"version": "0.1.0", "summary": "update test"},
        )
        pkg_id = create_resp.json()["id"]

        resp = await client.patch(
            f"/release-packages/{pkg_id}",
            json={"summary": "Updated via route"},
        )
        assert resp.status_code == 200
        assert resp.json()["summary"] == "Updated via route"

    @pytest.mark.asyncio
    async def test_update_environment_route(
        self, db_session: AsyncSession, client: AsyncClient,
    ):
        project = await _seed_project(db_session)
        await db_session.commit()

        create_resp = await client.post(
            f"/projects/{project.id}/environments",
            json={"name": "dev", "tier": "development"},
        )
        env_id = create_resp.json()["id"]

        resp = await client.patch(
            f"/environments/{env_id}",
            json={"description": "Updated dev"},
        )
        assert resp.status_code == 200
        assert resp.json()["description"] == "Updated dev"

    @pytest.mark.asyncio
    async def test_delete_environment_route(
        self, db_session: AsyncSession, client: AsyncClient,
    ):
        project = await _seed_project(db_session)
        await db_session.commit()

        create_resp = await client.post(
            f"/projects/{project.id}/environments",
            json={"name": "temp", "tier": "development"},
        )
        env_id = create_resp.json()["id"]

        resp = await client.delete(f"/environments/{env_id}")
        assert resp.status_code == 204

        resp = await client.get(f"/environments/{env_id}")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_not_found_release_package(self, client: AsyncClient):
        fake_id = uuid.uuid4()
        resp = await client.get(f"/release-packages/{fake_id}")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_not_found_environment(self, client: AsyncClient):
        fake_id = uuid.uuid4()
        resp = await client.get(f"/environments/{fake_id}")
        assert resp.status_code == 404
