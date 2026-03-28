"""Tests for Pydantic schema validation across all domain models."""

import uuid
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectRead
from app.schemas.run import RunRead
from app.schemas.task import TaskRead, TaskStatusUpdate, TaskClaimRequest, TaskFailRequest
from app.schemas.artifact import ArtifactCreate, ArtifactRead, ArtifactUpdate
from app.schemas.agent import AgentRead
from app.schemas.approval import ApprovalCreate, ApprovalDecision
from app.schemas.execution_event import ExecutionEventRead
from app.schemas.prompt_intake import PromptIntakeRequest
from app.schemas.connector import ConnectorRead, ConnectorRecommendation
from app.schemas.planner_result import PlannerResultRead


class TestProjectSchemas:
    """Validate Project request/response schemas."""

    def test_create_valid(self):
        data = ProjectCreate(name="My Project", description="A test project")
        assert data.name == "My Project"

    def test_create_empty_name_rejected(self):
        with pytest.raises(ValidationError):
            ProjectCreate(name="")

    def test_create_name_too_long_rejected(self):
        with pytest.raises(ValidationError):
            ProjectCreate(name="x" * 256)

    def test_update_partial(self):
        data = ProjectUpdate(name="Updated Name")
        dumped = data.model_dump(exclude_unset=True)
        assert "name" in dumped
        assert "description" not in dumped

    def test_read_from_dict(self):
        now = datetime.now(tz=timezone.utc)
        read = ProjectRead(
            id=uuid.uuid4(),
            name="Test",
            description=None,
            status="draft",
            owner_id=uuid.uuid4(),
            workspace_id=None,
            created_at=now,
            updated_at=now,
        )
        assert read.status == "draft"


class TestRunSchemas:
    """Validate Run response schemas."""

    def test_run_read(self):
        now = datetime.now(tz=timezone.utc)
        run = RunRead(
            id=uuid.uuid4(),
            run_number=1,
            status="pending",
            trigger="manual",
            project_id=uuid.uuid4(),
            created_at=now,
            updated_at=now,
        )
        assert run.run_number == 1
        assert run.trigger == "manual"


class TestTaskSchemas:
    """Validate Task request/response schemas."""

    def test_task_read(self):
        now = datetime.now(tz=timezone.utc)
        task = TaskRead(
            id=uuid.uuid4(),
            title="Design architecture",
            description="Create system architecture",
            task_type="architecture",
            status="ready",
            order_index=0,
            depends_on=None,
            parent_id=None,
            run_id=uuid.uuid4(),
            assigned_agent_slug=None,
            error_message=None,
            created_at=now,
            updated_at=now,
        )
        assert task.title == "Design architecture"

    def test_task_status_update(self):
        update = TaskStatusUpdate(status="running")
        assert update.status.value == "running"

    def test_task_claim_request(self):
        claim = TaskClaimRequest(agent_slug="architect")
        assert claim.agent_slug == "architect"

    def test_task_fail_request(self):
        fail = TaskFailRequest(error_message="LLM timeout")
        assert fail.error_message == "LLM timeout"


class TestArtifactSchemas:
    """Validate Artifact request/response schemas."""

    def test_create_minimal(self):
        data = ArtifactCreate(title="My Artifact")
        assert data.artifact_type.value == "other"
        assert data.content is None

    def test_create_empty_title_rejected(self):
        with pytest.raises(ValidationError):
            ArtifactCreate(title="")

    def test_update_partial(self):
        data = ArtifactUpdate(content="Updated content")
        dumped = data.model_dump(exclude_unset=True)
        assert "content" in dumped
        assert "title" not in dumped


class TestAgentSchemas:
    """Validate Agent response schemas."""

    def test_agent_read(self):
        now = datetime.now(tz=timezone.utc)
        agent = AgentRead(
            id=uuid.uuid4(),
            name="Architect Agent",
            slug="architect",
            description="Designs system architecture",
            status="active",
            capabilities=["system_design", "api_design"],
            supported_task_types=["architecture"],
            created_at=now,
            updated_at=now,
        )
        assert agent.slug == "architect"
        assert "system_design" in agent.capabilities


class TestApprovalSchemas:
    """Validate Approval request/response schemas."""

    def test_create(self):
        data = ApprovalCreate(
            title="Review architecture",
            project_id=uuid.uuid4(),
        )
        assert data.run_id is None

    def test_decision(self):
        decision = ApprovalDecision(
            status="approved",
            decided_by="operator",
            decision_comment="Looks good",
        )
        assert decision.status.value == "approved"

    def test_decision_rejected(self):
        decision = ApprovalDecision(
            status="rejected",
            decision_comment="Needs more detail",
        )
        assert decision.status.value == "rejected"


class TestPromptIntakeSchemas:
    """Validate PromptIntake request schemas."""

    def test_valid_prompt(self):
        data = PromptIntakeRequest(
            prompt="Build me a REST API for a task manager using FastAPI",
        )
        assert len(data.prompt) > 10

    def test_prompt_too_short_rejected(self):
        with pytest.raises(ValidationError):
            PromptIntakeRequest(prompt="Hi")

    def test_prompt_with_project_name(self):
        data = PromptIntakeRequest(
            prompt="Build a full-stack app with Next.js and FastAPI",
            project_name="My App",
        )
        assert data.project_name == "My App"


class TestConnectorSchemas:
    """Validate Connector schemas."""

    def test_recommendation(self):
        rec = ConnectorRecommendation(
            connector_slug="github",
            connector_name="GitHub",
            reason="Version control needed",
            priority="required",
            configured=False,
        )
        assert rec.priority == "required"
        assert not rec.configured


class TestPlannerResultSchemas:
    """Validate PlannerResult schemas with coercion validators."""

    def test_coerce_stack_values(self):
        now = datetime.now(tz=timezone.utc)
        result = PlannerResultRead(
            id=uuid.uuid4(),
            run_id=uuid.uuid4(),
            overview="Test overview",
            architecture_summary="Test arch",
            recommended_stack={"backend": "FastAPI", "database": "PostgreSQL"},
            assumptions=["User has Docker installed"],
            next_steps=["Set up CI/CD"],
            created_at=now,
            updated_at=now,
        )
        assert result.recommended_stack["backend"] == "FastAPI"

    def test_coerce_null_stack(self):
        now = datetime.now(tz=timezone.utc)
        result = PlannerResultRead(
            id=uuid.uuid4(),
            run_id=uuid.uuid4(),
            overview=None,
            architecture_summary=None,
            recommended_stack=None,
            assumptions=None,
            next_steps=None,
            created_at=now,
            updated_at=now,
        )
        assert result.recommended_stack is None
        assert result.assumptions is None


class TestExecutionEventSchemas:
    """Validate ExecutionEvent schemas."""

    def test_event_read(self):
        now = datetime.now(tz=timezone.utc)
        event = ExecutionEventRead(
            id=uuid.uuid4(),
            event_type="task_completed",
            summary="Task completed by architect agent",
            metadata_={"duration_ms": 1200},
            project_id=uuid.uuid4(),
            run_id=uuid.uuid4(),
            task_id=uuid.uuid4(),
            artifact_id=None,
            agent_slug="architect",
            created_at=now,
        )
        assert event.event_type.value == "task_completed"
        assert event.metadata_["duration_ms"] == 1200
