"""FM-121–130: Comprehensive tests for Execution Memory, Checkpoints,
Delivery Artifacts, and End-to-End Traceability.

Covers:
  FM-121: ExecutionCheckpoint data model + CRUD
  FM-122: Auto-checkpoint generation from run state
  FM-123: Resume from checkpoint
  FM-124: Delivery artifact generation
  FM-125: Review package generation
  FM-126: Traceability graph computation
  FM-127: Run memory enrichment
  FM-128: Release confidence scoring
  FM-129: Local CLI checkpoint/confidence/review
  FM-130: Integration hardening
"""

import uuid
from pathlib import Path

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import STUB_USER_ID


# ── Helpers ──────────────────────────────────────────────────────


async def _seed_project(db: AsyncSession, **kwargs):
    from app.models.project import Project
    from app.models.membership import ProjectMember, ProjectRole

    project = Project(
        name=kwargs.get("name", "Checkpoint Test Project"),
        description="For FM-121–130 tests",
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


async def _seed_artifact(
    db: AsyncSession, run_id: uuid.UUID, project_id: uuid.UUID, **kwargs
):
    from app.models.artifact import Artifact, ArtifactType

    artifact = Artifact(
        run_id=run_id,
        project_id=project_id,
        title=kwargs.get("title", "Test artifact"),
        artifact_type=kwargs.get("artifact_type", ArtifactType.SPEC),
        content=kwargs.get("content", "Spec content here"),
        created_by="test",
    )
    db.add(artifact)
    await db.flush()
    await db.refresh(artifact)
    return artifact


async def _seed_approval(
    db: AsyncSession, run_id: uuid.UUID, project_id: uuid.UUID, **kwargs
):
    from app.models.approval_request import ApprovalRequest, ApprovalStatus

    approval = ApprovalRequest(
        run_id=run_id,
        project_id=project_id,
        title=kwargs.get("title", "Approve spec"),
        description=kwargs.get("description", "Please approve"),
        status=kwargs.get("status", ApprovalStatus.PENDING),
    )
    db.add(approval)
    await db.flush()
    await db.refresh(approval)
    return approval


async def _setup_full_run(db: AsyncSession):
    """Seed a complete run with tasks, artifacts, and approvals."""
    from app.models.artifact import ArtifactType
    from app.models.task import TaskStatus
    from app.models.approval_request import ApprovalStatus

    project = await _seed_project(db)
    run = await _seed_run(db, project.id)

    # Tasks
    t1 = await _seed_task(db, run.id, title="Design API", status=TaskStatus.COMPLETED)
    t2 = await _seed_task(
        db, run.id, title="Implement core", status=TaskStatus.COMPLETED
    )
    t3 = await _seed_task(db, run.id, title="Write tests", status=TaskStatus.READY)

    # Artifacts
    spec = await _seed_artifact(
        db,
        run.id,
        project.id,
        title="SPEC",
        artifact_type=ArtifactType.SPEC,
        content="# Spec\nBuild a widget.",
    )
    plan = await _seed_artifact(
        db,
        run.id,
        project.id,
        title="PLAN",
        artifact_type=ArtifactType.PLAN,
        content="# Plan\n1. Design\n2. Build",
    )

    # Approval
    approval = await _seed_approval(
        db, run.id, project.id, title="Approve spec", status=ApprovalStatus.APPROVED
    )

    return {
        "project": project,
        "run": run,
        "tasks": [t1, t2, t3],
        "spec": spec,
        "plan": plan,
        "approval": approval,
    }


# ═════════════════════════════════════════════════════════════════
# FM-121: ExecutionCheckpoint CRUD
# ═════════════════════════════════════════════════════════════════


class TestCheckpointService:
    """FM-121: Checkpoint CRUD via service layer."""

    @pytest.mark.asyncio
    async def test_create_checkpoint(self, db_session: AsyncSession):
        from app.services import execution_checkpoint_service as svc
        from app.models.execution_checkpoint import CheckpointType

        project = await _seed_project(db_session)
        run = await _seed_run(db_session, project.id)

        checkpoint = await svc.create_checkpoint(
            db_session,
            run_id=run.id,
            project_id=project.id,
            checkpoint_type=CheckpointType.MANUAL,
            summary="Initial manual checkpoint",
            created_by="test",
        )
        assert checkpoint.id is not None
        assert checkpoint.summary == "Initial manual checkpoint"
        assert checkpoint.checkpoint_type == CheckpointType.MANUAL
        assert checkpoint.sequence_number == 0

    @pytest.mark.asyncio
    async def test_list_checkpoints(self, db_session: AsyncSession):
        from app.services import execution_checkpoint_service as svc
        from app.models.execution_checkpoint import CheckpointType

        project = await _seed_project(db_session)
        run = await _seed_run(db_session, project.id)

        await svc.create_checkpoint(
            db_session,
            run_id=run.id,
            project_id=project.id,
            checkpoint_type=CheckpointType.MANUAL,
            summary="First",
            created_by="test",
        )
        await svc.create_checkpoint(
            db_session,
            run_id=run.id,
            project_id=project.id,
            checkpoint_type=CheckpointType.AUTO_PHASE,
            summary="Second",
            created_by="test",
        )

        items, total = await svc.list_checkpoints(db_session, run.id)
        assert total == 2
        assert len(items) == 2
        assert items[0].sequence_number == 0
        assert items[1].sequence_number == 1

    @pytest.mark.asyncio
    async def test_get_latest_checkpoint(self, db_session: AsyncSession):
        from app.services import execution_checkpoint_service as svc
        from app.models.execution_checkpoint import CheckpointType

        project = await _seed_project(db_session)
        run = await _seed_run(db_session, project.id)

        await svc.create_checkpoint(
            db_session,
            run_id=run.id,
            project_id=project.id,
            checkpoint_type=CheckpointType.MANUAL,
            summary="First",
            created_by="test",
        )
        await svc.create_checkpoint(
            db_session,
            run_id=run.id,
            project_id=project.id,
            checkpoint_type=CheckpointType.AUTO_PHASE,
            summary="Latest",
            created_by="test",
        )

        latest = await svc.get_latest_checkpoint(db_session, run.id)
        assert latest is not None
        assert latest.summary == "Latest"
        assert latest.sequence_number == 1

    @pytest.mark.asyncio
    async def test_get_checkpoint_by_id(self, db_session: AsyncSession):
        from app.services import execution_checkpoint_service as svc
        from app.models.execution_checkpoint import CheckpointType

        project = await _seed_project(db_session)
        run = await _seed_run(db_session, project.id)

        cp = await svc.create_checkpoint(
            db_session,
            run_id=run.id,
            project_id=project.id,
            checkpoint_type=CheckpointType.MANUAL,
            summary="Test",
            created_by="test",
        )
        fetched = await svc.get_checkpoint(db_session, cp.id)
        assert fetched is not None
        assert fetched.id == cp.id

    @pytest.mark.asyncio
    async def test_checkpoint_with_snapshots(self, db_session: AsyncSession):
        from app.services import execution_checkpoint_service as svc
        from app.models.execution_checkpoint import CheckpointType

        project = await _seed_project(db_session)
        run = await _seed_run(db_session, project.id)

        cp = await svc.create_checkpoint(
            db_session,
            run_id=run.id,
            project_id=project.id,
            checkpoint_type=CheckpointType.PRE_DELIVERY,
            summary="Delivery checkpoint",
            status_snapshot={"total_tasks": 5, "task_counts": {"completed": 3}},
            artifact_refs={"artifacts": [{"id": "abc", "title": "SPEC"}]},
            created_by="test",
        )
        assert cp.status_snapshot["total_tasks"] == 5
        assert len(cp.artifact_refs["artifacts"]) == 1


# ═════════════════════════════════════════════════════════════════
# FM-122: Auto-checkpoint generation
# ═════════════════════════════════════════════════════════════════


class TestAutoCheckpoint:
    """FM-122: Auto-checkpoint with computed snapshots."""

    @pytest.mark.asyncio
    async def test_auto_checkpoint_captures_state(self, db_session: AsyncSession):
        from app.services import execution_checkpoint_service as svc
        from app.models.execution_checkpoint import CheckpointType

        data = await _setup_full_run(db_session)
        run = data["run"]
        project = data["project"]

        cp = await svc.create_auto_checkpoint(
            db_session,
            run_id=run.id,
            project_id=project.id,
            checkpoint_type=CheckpointType.AUTO_PHASE,
            summary="Phase transition checkpoint",
        )

        assert cp.status_snapshot is not None
        assert cp.status_snapshot["total_tasks"] == 3
        assert cp.artifact_refs is not None
        assert cp.approval_snapshot is not None
        assert cp.approval_snapshot["total"] == 1
        assert cp.created_by == "system"

    @pytest.mark.asyncio
    async def test_auto_checkpoint_with_task_ref(self, db_session: AsyncSession):
        from app.services import execution_checkpoint_service as svc
        from app.models.execution_checkpoint import CheckpointType

        data = await _setup_full_run(db_session)
        run = data["run"]
        project = data["project"]
        task = data["tasks"][0]

        cp = await svc.create_auto_checkpoint(
            db_session,
            run_id=run.id,
            project_id=project.id,
            checkpoint_type=CheckpointType.PRE_APPROVAL,
            summary="Pre-approval checkpoint",
            task_id=task.id,
        )

        assert cp.task_id == task.id


# ═════════════════════════════════════════════════════════════════
# FM-123: Resume from checkpoint
# ═════════════════════════════════════════════════════════════════


class TestResumeCheckpoint:
    """FM-123: Resume semantics from checkpoint."""

    @pytest.mark.asyncio
    async def test_resume_success(self, db_session: AsyncSession):
        from app.services import execution_checkpoint_service as svc
        from app.models.execution_checkpoint import CheckpointType

        data = await _setup_full_run(db_session)
        run = data["run"]
        project = data["project"]

        cp = await svc.create_auto_checkpoint(
            db_session,
            run_id=run.id,
            project_id=project.id,
            checkpoint_type=CheckpointType.AUTO_PHASE,
            summary="Checkpoint to resume from",
        )

        result = await svc.resume_from_checkpoint(
            db_session, run_id=run.id, checkpoint_id=cp.id
        )

        assert result["resumed"] is True
        ctx = result["context"]
        assert ctx["checkpoint_id"] == str(cp.id)
        assert "completed_at_checkpoint" in ctx
        assert "current_state" in ctx
        assert "pending_tasks" in ctx

    @pytest.mark.asyncio
    async def test_resume_wrong_run(self, db_session: AsyncSession):
        from app.services import execution_checkpoint_service as svc
        from app.models.execution_checkpoint import CheckpointType

        data = await _setup_full_run(db_session)
        run = data["run"]
        project = data["project"]

        cp = await svc.create_checkpoint(
            db_session,
            run_id=run.id,
            project_id=project.id,
            checkpoint_type=CheckpointType.MANUAL,
            summary="Test",
            created_by="test",
        )

        other_run_id = uuid.uuid4()
        result = await svc.resume_from_checkpoint(
            db_session, run_id=other_run_id, checkpoint_id=cp.id
        )
        assert result["error"] == "checkpoint_does_not_belong_to_run"

    @pytest.mark.asyncio
    async def test_resume_not_found(self, db_session: AsyncSession):
        from app.services import execution_checkpoint_service as svc

        result = await svc.resume_from_checkpoint(
            db_session, run_id=uuid.uuid4(), checkpoint_id=uuid.uuid4()
        )
        assert result["error"] == "checkpoint_not_found"


# ═════════════════════════════════════════════════════════════════
# FM-124: Delivery artifact generation
# ═════════════════════════════════════════════════════════════════


class TestDeliveryArtifacts:
    """FM-124: Delivery artifact generation from run state."""

    @pytest.mark.asyncio
    async def test_generate_implementation_summary(self, db_session: AsyncSession):
        from app.services import delivery_artifact_service as svc

        data = await _setup_full_run(db_session)
        run = data["run"]

        artifact = await svc.generate_delivery_artifact(
            db_session,
            run_id=run.id,
            project_id=data["project"].id,
            artifact_kind="implementation_summary",
        )

        assert artifact.id is not None
        assert "Implementation Summary" in artifact.title
        assert "# Implementation Summary" in artifact.content
        assert "Design API" in artifact.content

    @pytest.mark.asyncio
    async def test_generate_changelog_draft(self, db_session: AsyncSession):
        from app.services import delivery_artifact_service as svc

        data = await _setup_full_run(db_session)
        artifact = await svc.generate_delivery_artifact(
            db_session,
            run_id=data["run"].id,
            project_id=data["project"].id,
            artifact_kind="changelog_draft",
        )
        assert "Changelog" in artifact.title
        assert "Design API" in artifact.content

    @pytest.mark.asyncio
    async def test_generate_release_note_draft(self, db_session: AsyncSession):
        from app.services import delivery_artifact_service as svc

        data = await _setup_full_run(db_session)
        artifact = await svc.generate_delivery_artifact(
            db_session,
            run_id=data["run"].id,
            project_id=data["project"].id,
            artifact_kind="release_note_draft",
        )
        assert "Release Note" in artifact.title
        assert "2 of 3" in artifact.content

    @pytest.mark.asyncio
    async def test_invalid_kind_raises(self, db_session: AsyncSession):
        from app.services import delivery_artifact_service as svc

        data = await _setup_full_run(db_session)
        with pytest.raises(ValueError, match="Unknown delivery artifact kind"):
            await svc.generate_delivery_artifact(
                db_session,
                run_id=data["run"].id,
                project_id=data["project"].id,
                artifact_kind="nonexistent_kind",
            )


# ═════════════════════════════════════════════════════════════════
# FM-125: Review package
# ═════════════════════════════════════════════════════════════════


class TestReviewPackage:
    """FM-125: Review package generation."""

    @pytest.mark.asyncio
    async def test_generate_review_package(self, db_session: AsyncSession):
        from app.services import delivery_artifact_service as svc
        from app.models.artifact import ArtifactType

        data = await _setup_full_run(db_session)
        artifact = await svc.generate_review_package(
            db_session, run_id=data["run"].id, project_id=data["project"].id
        )

        assert artifact.id is not None
        assert artifact.artifact_type == ArtifactType.REVIEW
        assert "Review Package" in artifact.title
        assert "Task Completion Snapshot" in artifact.content
        assert "Approval State" in artifact.content
        assert "Open Risks" in artifact.content

    @pytest.mark.asyncio
    async def test_review_package_identifies_risks(self, db_session: AsyncSession):
        from app.services import delivery_artifact_service as svc

        data = await _setup_full_run(db_session)
        artifact = await svc.generate_review_package(
            db_session, run_id=data["run"].id, project_id=data["project"].id
        )
        # One task is still READY → risk
        assert (
            "1/3 tasks completed" in artifact.content
            or "Only 2/3 tasks completed" in artifact.content
        )


# ═════════════════════════════════════════════════════════════════
# FM-126: Traceability graph
# ═════════════════════════════════════════════════════════════════


class TestTraceability:
    """FM-126: End-to-end traceability graph computation."""

    @pytest.mark.asyncio
    async def test_graph_has_expected_nodes(self, db_session: AsyncSession):
        from app.services import traceability_service as svc

        data = await _setup_full_run(db_session)
        graph = await svc.compute_traceability(db_session, data["run"].id)

        assert graph["node_count"] > 0
        assert graph["edge_count"] > 0

        node_types = {n["type"] for n in graph["nodes"]}
        assert "run" in node_types
        assert "artifact" in node_types
        assert "task" in node_types

    @pytest.mark.asyncio
    async def test_graph_includes_checkpoints(self, db_session: AsyncSession):
        from app.services import traceability_service as svc
        from app.services import execution_checkpoint_service as cp_svc
        from app.models.execution_checkpoint import CheckpointType

        data = await _setup_full_run(db_session)
        await cp_svc.create_auto_checkpoint(
            db_session,
            run_id=data["run"].id,
            project_id=data["project"].id,
            checkpoint_type=CheckpointType.AUTO_PHASE,
            summary="Phase checkpoint",
        )

        graph = await svc.compute_traceability(db_session, data["run"].id)
        node_types = {n["type"] for n in graph["nodes"]}
        assert "checkpoint" in node_types

    @pytest.mark.asyncio
    async def test_graph_not_found(self, db_session: AsyncSession):
        from app.services import traceability_service as svc

        result = await svc.compute_traceability(db_session, uuid.uuid4())
        assert result["error"] == "run_not_found"

    @pytest.mark.asyncio
    async def test_graph_edges_connect_nodes(self, db_session: AsyncSession):
        from app.services import traceability_service as svc

        data = await _setup_full_run(db_session)
        graph = await svc.compute_traceability(db_session, data["run"].id)

        node_ids = {n["id"] for n in graph["nodes"]}
        for edge in graph["edges"]:
            assert edge["from"] in node_ids
            assert edge["to"] in node_ids


# ═════════════════════════════════════════════════════════════════
# FM-127: Run memory enrichment
# ═════════════════════════════════════════════════════════════════


class TestRunMemoryEnrichment:
    """FM-127: Structured run memory enrichment."""

    @pytest.mark.asyncio
    async def test_enrichment_structure(self, db_session: AsyncSession):
        from app.services import run_memory_enrichment_service as svc

        data = await _setup_full_run(db_session)
        result = await svc.enrich_run_memory(db_session, data["run"].id)

        assert "completed_objectives" in result
        assert "unresolved_blockers" in result
        assert "validation_outcomes" in result
        assert "confidence_factors" in result
        assert "delivery_notes" in result

    @pytest.mark.asyncio
    async def test_enrichment_completed_objectives(self, db_session: AsyncSession):
        from app.services import run_memory_enrichment_service as svc

        data = await _setup_full_run(db_session)
        result = await svc.enrich_run_memory(db_session, data["run"].id)

        assert len(result["completed_objectives"]) == 2  # 2 completed tasks
        titles = {o["title"] for o in result["completed_objectives"]}
        assert "Design API" in titles
        assert "Implement core" in titles

    @pytest.mark.asyncio
    async def test_enrichment_validation_outcomes(self, db_session: AsyncSession):
        from app.services import run_memory_enrichment_service as svc

        data = await _setup_full_run(db_session)
        result = await svc.enrich_run_memory(db_session, data["run"].id)

        vo = result["validation_outcomes"]
        assert vo["has_spec"] is True
        assert vo["has_plan"] is True
        assert vo["tasks_completed"] == 2
        assert vo["tasks_total"] == 3

    @pytest.mark.asyncio
    async def test_enrichment_not_found(self, db_session: AsyncSession):
        from app.services import run_memory_enrichment_service as svc

        result = await svc.enrich_run_memory(db_session, uuid.uuid4())
        assert result["error"] == "run_not_found"


# ═════════════════════════════════════════════════════════════════
# FM-128: Release confidence scoring
# ═════════════════════════════════════════════════════════════════


class TestReleaseConfidence:
    """FM-128: Explainable release confidence scoring."""

    @pytest.mark.asyncio
    async def test_confidence_structure(self, db_session: AsyncSession):
        from app.services import release_confidence_service as svc

        data = await _setup_full_run(db_session)
        result = await svc.compute_release_confidence(db_session, data["run"].id)

        assert "score" in result
        assert "band" in result
        assert "reasons" in result
        assert "blocking_factors" in result
        assert "suggested_actions" in result
        assert 0 <= result["score"] <= 100

    @pytest.mark.asyncio
    async def test_confidence_partial_completion(self, db_session: AsyncSession):
        from app.services import release_confidence_service as svc

        data = await _setup_full_run(db_session)
        result = await svc.compute_release_confidence(db_session, data["run"].id)

        # 2/3 tasks completed, run still running → not perfect
        assert result["score"] < 100
        assert result["band"] in ("low", "medium", "high")
        # Should have blocking factors
        assert len(result["blocking_factors"]) > 0

    @pytest.mark.asyncio
    async def test_confidence_complete_run(self, db_session: AsyncSession):
        from app.services import release_confidence_service as svc
        from app.models.run import RunStatus
        from app.models.task import TaskStatus
        from app.models.artifact import ArtifactType
        from app.models.approval_request import ApprovalStatus
        from app.services import execution_checkpoint_service as cp_svc
        from app.models.execution_checkpoint import CheckpointType

        project = await _seed_project(db_session)
        run = await _seed_run(db_session, project.id, status=RunStatus.COMPLETED)

        await _seed_task(
            db_session, run.id, title="Task 1", status=TaskStatus.COMPLETED
        )
        await _seed_artifact(
            db_session,
            run.id,
            project.id,
            title="SPEC",
            artifact_type=ArtifactType.SPEC,
        )
        await _seed_artifact(
            db_session,
            run.id,
            project.id,
            title="PLAN",
            artifact_type=ArtifactType.PLAN,
        )
        await _seed_approval(
            db_session, run.id, project.id, status=ApprovalStatus.APPROVED
        )
        await cp_svc.create_checkpoint(
            db_session,
            run_id=run.id,
            project_id=project.id,
            checkpoint_type=CheckpointType.MANUAL,
            summary="cp",
            created_by="test",
        )

        result = await svc.compute_release_confidence(db_session, run.id)
        assert result["score"] >= 80
        assert result["band"] == "high"

    @pytest.mark.asyncio
    async def test_confidence_not_found(self, db_session: AsyncSession):
        from app.services import release_confidence_service as svc

        result = await svc.compute_release_confidence(db_session, uuid.uuid4())
        assert result["error"] == "run_not_found"

    @pytest.mark.asyncio
    async def test_confidence_reasons_signal_names(self, db_session: AsyncSession):
        from app.services import release_confidence_service as svc

        data = await _setup_full_run(db_session)
        result = await svc.compute_release_confidence(db_session, data["run"].id)

        signal_names = {r["signal"] for r in result["reasons"]}
        expected_signals = {
            "task_completion",
            "spec_present",
            "plan_present",
            "approvals_resolved",
            "no_rejections",
            "has_checkpoints",
            "run_completed",
            "has_delivery_artifacts",
        }
        assert signal_names == expected_signals


# ═════════════════════════════════════════════════════════════════
# FM-121/130: HTTP API integration tests
# ═════════════════════════════════════════════════════════════════


class TestCheckpointAPI:
    """HTTP-level integration tests for checkpoint endpoints."""

    @pytest.mark.asyncio
    async def test_create_checkpoint_http(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        data = await _setup_full_run(db_session)
        await db_session.commit()

        resp = await client.post(
            f"/runs/{data['run'].id}/checkpoints",
            json={
                "checkpoint_type": "manual",
                "summary": "HTTP test checkpoint",
            },
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["summary"] == "HTTP test checkpoint"
        assert body["checkpoint_type"] == "manual"
        assert body["sequence_number"] == 0

    @pytest.mark.asyncio
    async def test_list_checkpoints_http(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        data = await _setup_full_run(db_session)
        await db_session.commit()

        await client.post(
            f"/runs/{data['run'].id}/checkpoints",
            json={"checkpoint_type": "manual", "summary": "cp1"},
        )
        await client.post(
            f"/runs/{data['run'].id}/checkpoints",
            json={"checkpoint_type": "auto_phase", "summary": "cp2"},
        )

        resp = await client.get(f"/runs/{data['run'].id}/checkpoints")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 2
        assert len(body["items"]) == 2

    @pytest.mark.asyncio
    async def test_get_latest_checkpoint_http(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        data = await _setup_full_run(db_session)
        await db_session.commit()

        await client.post(
            f"/runs/{data['run'].id}/checkpoints",
            json={"checkpoint_type": "manual", "summary": "first"},
        )
        await client.post(
            f"/runs/{data['run'].id}/checkpoints",
            json={"checkpoint_type": "manual", "summary": "latest"},
        )

        resp = await client.get(f"/runs/{data['run'].id}/checkpoints/latest")
        assert resp.status_code == 200
        assert resp.json()["summary"] == "latest"

    @pytest.mark.asyncio
    async def test_resume_checkpoint_http(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        data = await _setup_full_run(db_session)
        await db_session.commit()

        cp_resp = await client.post(
            f"/runs/{data['run'].id}/checkpoints",
            json={"checkpoint_type": "manual", "summary": "resume target"},
        )
        cp_id = cp_resp.json()["id"]

        resp = await client.post(
            f"/runs/{data['run'].id}/checkpoints/{cp_id}/resume",
        )
        assert resp.status_code == 200
        assert resp.json()["resumed"] is True


class TestDeliveryAPI:
    """HTTP-level integration tests for delivery endpoints."""

    @pytest.mark.asyncio
    async def test_generate_delivery_artifact_http(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        data = await _setup_full_run(db_session)
        await db_session.commit()

        resp = await client.post(
            f"/runs/{data['run'].id}/delivery-artifacts?kind=implementation_summary"
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["delivery_kind"] == "implementation_summary"
        assert "id" in body

    @pytest.mark.asyncio
    async def test_generate_review_package_http(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        data = await _setup_full_run(db_session)
        await db_session.commit()

        resp = await client.post(f"/runs/{data['run'].id}/review-package")
        assert resp.status_code == 201
        body = resp.json()
        assert "Review Package" in body["title"]

    @pytest.mark.asyncio
    async def test_traceability_http(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        data = await _setup_full_run(db_session)
        await db_session.commit()

        resp = await client.get(f"/runs/{data['run'].id}/traceability")
        assert resp.status_code == 200
        body = resp.json()
        assert body["node_count"] > 0
        assert body["edge_count"] > 0

    @pytest.mark.asyncio
    async def test_run_memory_http(self, client: AsyncClient, db_session: AsyncSession):
        data = await _setup_full_run(db_session)
        await db_session.commit()

        resp = await client.get(f"/runs/{data['run'].id}/memory")
        assert resp.status_code == 200
        body = resp.json()
        assert "completed_objectives" in body
        assert "confidence_factors" in body

    @pytest.mark.asyncio
    async def test_confidence_http(self, client: AsyncClient, db_session: AsyncSession):
        data = await _setup_full_run(db_session)
        await db_session.commit()

        resp = await client.get(f"/runs/{data['run'].id}/confidence")
        assert resp.status_code == 200
        body = resp.json()
        assert "score" in body
        assert "band" in body
        assert "reasons" in body


# ═════════════════════════════════════════════════════════════════
# FM-129: Local CLI checkpoint / confidence / review
# ═════════════════════════════════════════════════════════════════


class TestLocalCLICommands:
    """FM-129: Local CLI commands for checkpoints, confidence, and review."""

    def test_checkpoint_save_and_list(self, tmp_path: Path):
        from click.testing import CliRunner
        from forgemind_local.cli import main
        from forgemind_local.config import LocalConfig, save_config

        # Set up local workspace
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        cfg = LocalConfig.default(str(tmp_path))
        save_config(cfg)

        runner = CliRunner()
        run_id = "test-run-001"

        # Save a checkpoint
        result = runner.invoke(
            main,
            [
                "checkpoint",
                "save",
                run_id,
                "--summary",
                "Test CP",
                "--path",
                str(tmp_path),
            ],
        )
        assert result.exit_code == 0
        assert "Checkpoint #1 saved" in result.output

        # Save another
        result = runner.invoke(
            main,
            [
                "checkpoint",
                "save",
                run_id,
                "--summary",
                "Second CP",
                "--path",
                str(tmp_path),
            ],
        )
        assert result.exit_code == 0

        # List
        result = runner.invoke(
            main,
            ["checkpoint", "list", run_id, "--path", str(tmp_path)],
        )
        assert result.exit_code == 0
        assert "Test CP" in result.output or "manual" in result.output

    def test_confidence_no_data(self, tmp_path: Path):
        from click.testing import CliRunner
        from forgemind_local.cli import main
        from forgemind_local.config import LocalConfig, save_config

        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        cfg = LocalConfig.default(str(tmp_path))
        save_config(cfg)

        runner = CliRunner()
        result = runner.invoke(
            main,
            ["confidence", "test-run", "--path", str(tmp_path)],
        )
        assert result.exit_code == 0
        assert "Score:" in result.output

    def test_review_no_data(self, tmp_path: Path):
        from click.testing import CliRunner
        from forgemind_local.cli import main
        from forgemind_local.config import LocalConfig, save_config

        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        cfg = LocalConfig.default(str(tmp_path))
        save_config(cfg)

        runner = CliRunner()
        result = runner.invoke(
            main,
            ["review", "test-run", "--path", str(tmp_path)],
        )
        assert result.exit_code == 0
        assert "No local run data" in result.output


# ═════════════════════════════════════════════════════════════════
# FM-130: Integration hardening
# ═════════════════════════════════════════════════════════════════


class TestIntegrationHardening:
    """FM-130: Cross-service integration tests."""

    @pytest.mark.asyncio
    async def test_checkpoint_to_traceability(self, db_session: AsyncSession):
        """Checkpoints appear in traceability graph."""
        from app.services import execution_checkpoint_service as cp_svc
        from app.services import traceability_service as trace_svc
        from app.models.execution_checkpoint import CheckpointType

        data = await _setup_full_run(db_session)
        await cp_svc.create_auto_checkpoint(
            db_session,
            run_id=data["run"].id,
            project_id=data["project"].id,
            checkpoint_type=CheckpointType.AUTO_PHASE,
            summary="Phase checkpoint",
        )

        graph = await trace_svc.compute_traceability(db_session, data["run"].id)
        cp_nodes = [n for n in graph["nodes"] if n["type"] == "checkpoint"]
        assert len(cp_nodes) == 1
        assert cp_nodes[0]["subtype"] == "auto_phase"

    @pytest.mark.asyncio
    async def test_delivery_artifacts_boost_confidence(self, db_session: AsyncSession):
        """Delivery artifacts increase confidence score."""
        from app.services import release_confidence_service as conf_svc
        from app.services import delivery_artifact_service as del_svc

        data = await _setup_full_run(db_session)

        score_before = (
            await conf_svc.compute_release_confidence(db_session, data["run"].id)
        )["score"]

        await del_svc.generate_delivery_artifact(
            db_session,
            run_id=data["run"].id,
            project_id=data["project"].id,
            artifact_kind="implementation_summary",
        )

        score_after = (
            await conf_svc.compute_release_confidence(db_session, data["run"].id)
        )["score"]
        assert score_after >= score_before

    @pytest.mark.asyncio
    async def test_enrichment_reflects_checkpoints(self, db_session: AsyncSession):
        """Run memory enrichment includes checkpoint count."""
        from app.services import run_memory_enrichment_service as mem_svc
        from app.services import execution_checkpoint_service as cp_svc
        from app.models.execution_checkpoint import CheckpointType

        data = await _setup_full_run(db_session)
        await cp_svc.create_checkpoint(
            db_session,
            run_id=data["run"].id,
            project_id=data["project"].id,
            checkpoint_type=CheckpointType.MANUAL,
            summary="test",
            created_by="test",
        )

        result = await mem_svc.enrich_run_memory(db_session, data["run"].id)
        assert result["metadata"]["checkpoint_count"] == 1

    @pytest.mark.asyncio
    async def test_full_lifecycle_flow(self, db_session: AsyncSession):
        """End-to-end: create checkpoint → delivery → review → confidence → traceability → enrichment."""
        from app.services import execution_checkpoint_service as cp_svc
        from app.services import delivery_artifact_service as del_svc
        from app.services import traceability_service as trace_svc
        from app.services import run_memory_enrichment_service as mem_svc
        from app.services import release_confidence_service as conf_svc
        from app.models.execution_checkpoint import CheckpointType

        data = await _setup_full_run(db_session)
        run_id = data["run"].id
        project_id = data["project"].id

        # 1. Create checkpoint
        cp = await cp_svc.create_auto_checkpoint(
            db_session,
            run_id=run_id,
            project_id=project_id,
            checkpoint_type=CheckpointType.AUTO_PHASE,
            summary="Full lifecycle test",
        )
        assert cp.id is not None

        # 2. Generate delivery artifact
        delivery = await del_svc.generate_delivery_artifact(
            db_session,
            run_id=run_id,
            project_id=project_id,
            artifact_kind="implementation_summary",
        )
        assert delivery.id is not None

        # 3. Generate review package
        review = await del_svc.generate_review_package(
            db_session, run_id=run_id, project_id=project_id
        )
        assert review.id is not None

        # 4. Compute traceability
        graph = await trace_svc.compute_traceability(db_session, run_id)
        assert (
            graph["node_count"] >= 8
        )  # run + 2 orig artifacts + 3 tasks + 1 cp + 2 delivery

        # 5. Enrich memory
        memory = await mem_svc.enrich_run_memory(db_session, run_id)
        assert len(memory["completed_objectives"]) == 2
        assert memory["metadata"]["checkpoint_count"] == 1

        # 6. Compute confidence
        confidence = await conf_svc.compute_release_confidence(db_session, run_id)
        assert confidence["score"] > 0
        assert len(confidence["reasons"]) == 8
