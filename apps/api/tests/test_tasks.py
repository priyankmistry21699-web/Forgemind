"""Tests for Task API endpoints — lifecycle management."""

import uuid

import pytest
from app.models.task import TaskStatus


class TestListTasks:
    """GET /runs/{run_id}/tasks"""

    async def test_list_tasks(self, client, sample_run, sample_task):
        resp = await client.get(f"/runs/{sample_run.id}/tasks")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        assert data["items"][0]["title"] == "Test Task"

    async def test_list_tasks_empty_run(self, client, sample_run):
        resp = await client.get(f"/runs/{sample_run.id}/tasks")
        assert resp.status_code == 200


class TestGetTask:
    """GET /tasks/{task_id}"""

    async def test_get_task_success(self, client, sample_task):
        resp = await client.get(f"/tasks/{sample_task.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "Test Task"
        assert data["status"] == "ready"
        assert data["task_type"] == "architecture"

    async def test_get_task_not_found(self, client):
        resp = await client.get(f"/tasks/{uuid.uuid4()}")
        assert resp.status_code == 404


class TestReadyTasks:
    """GET /runs/{run_id}/tasks/ready"""

    async def test_ready_tasks(self, client, sample_run, sample_task):
        resp = await client.get(f"/runs/{sample_run.id}/tasks/ready")
        assert resp.status_code == 200
        data = resp.json()
        # sample_task is READY with no dependencies
        assert data["total"] >= 1
        assert all(t["status"] == "ready" for t in data["items"])


class TestTaskStatusUpdate:
    """PATCH /tasks/{task_id}/status"""

    async def test_update_status_to_running(self, client, sample_task):
        resp = await client.patch(
            f"/tasks/{sample_task.id}/status",
            json={"status": "running"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "running"


class TestTaskClaim:
    """POST /tasks/{task_id}/claim"""

    async def test_claim_task(self, client, db_session, sample_task):
        # Seed a test agent so claim can find it
        from app.models.agent import Agent, AgentStatus

        agent = Agent(
            slug="architect",
            name="Architect Agent",
            description="Designs system architecture",
            status=AgentStatus.ACTIVE,
            capabilities=["architecture", "design"],
            supported_task_types=["architecture"],
        )
        db_session.add(agent)
        await db_session.flush()

        resp = await client.post(
            f"/tasks/{sample_task.id}/claim",
            json={"agent_slug": "architect"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "running"
        assert data["assigned_agent_slug"] == "architect"


class TestTaskComplete:
    """POST /tasks/{task_id}/complete"""

    async def test_complete_task_with_artifact(self, client, db_session, sample_task):
        # First claim the task to set it RUNNING
        from app.models.task import Task, TaskStatus

        sample_task.status = TaskStatus.RUNNING
        sample_task.assigned_agent_slug = "architect"
        await db_session.flush()

        resp = await client.post(
            f"/tasks/{sample_task.id}/complete",
            json={
                "artifact_title": "Architecture Doc",
                "artifact_content": "# System Architecture",
                "artifact_type": "architecture",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "completed"


class TestTaskFail:
    """POST /tasks/{task_id}/fail"""

    async def test_fail_task(self, client, db_session, sample_task):
        # Set task to RUNNING first
        from app.models.task import Task, TaskStatus

        sample_task.status = TaskStatus.RUNNING
        sample_task.assigned_agent_slug = "coder"
        await db_session.flush()

        resp = await client.post(
            f"/tasks/{sample_task.id}/fail",
            json={"error_message": "LLM API timeout"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "failed"
        assert "LLM API timeout" in data["error_message"]


class TestTaskRetry:
    """POST /tasks/{task_id}/retry"""

    async def test_retry_failed_task(self, client, db_session, sample_task):
        # Set task to FAILED
        from app.models.task import Task, TaskStatus

        sample_task.status = TaskStatus.FAILED
        sample_task.error_message = "Previous error"
        await db_session.flush()

        resp = await client.post(f"/tasks/{sample_task.id}/retry")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ready"


class TestTaskCancel:
    """POST /tasks/{task_id}/cancel"""

    async def test_cancel_ready_task(self, client, sample_task):
        resp = await client.post(f"/tasks/{sample_task.id}/cancel")
        assert resp.status_code == 200
        assert resp.json()["status"] == "skipped"
