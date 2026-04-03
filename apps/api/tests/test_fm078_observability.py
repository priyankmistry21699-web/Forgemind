"""FM-078: Observability and metrics tests."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestMetrics:
    async def test_metrics_endpoint_exists(self, client: AsyncClient):
        """The /metrics endpoint should return Prometheus-format text."""
        resp = await client.get("/metrics")
        assert resp.status_code == 200
        assert "text/plain" in resp.headers.get("content-type", "")

    async def test_metrics_after_request(self, client: AsyncClient):
        """After making a request, counters should appear in /metrics."""
        # Make a request that registers metrics
        await client.get("/health")
        resp = await client.get("/metrics")
        body = resp.text
        assert "http_requests_total" in body
        assert "http_request_duration_seconds" in body

    async def test_counter_increment(self):
        """Counter should increment correctly."""
        from app.core.metrics import inc_counter, get_counter, reset_metrics

        reset_metrics()

        inc_counter("test_counter")
        assert get_counter("test_counter") == 1.0

        inc_counter("test_counter", 5.0)
        assert get_counter("test_counter") == 6.0

        reset_metrics()

    async def test_labeled_counter(self):
        """Labeled counters should track independently."""
        from app.core.metrics import inc_counter, get_counter, reset_metrics

        reset_metrics()

        inc_counter("req", labels={"method": "GET", "path": "/a"})
        inc_counter("req", labels={"method": "POST", "path": "/b"})
        inc_counter("req", labels={"method": "GET", "path": "/a"})

        assert get_counter("req", labels={"method": "GET", "path": "/a"}) == 2.0
        assert get_counter("req", labels={"method": "POST", "path": "/b"}) == 1.0

        reset_metrics()

    async def test_histogram_observation(self):
        """Histogram should bucket observations correctly."""
        from app.core.metrics import observe_histogram, render_prometheus, reset_metrics

        reset_metrics()

        observe_histogram("test_hist", 0.05)
        observe_histogram("test_hist", 0.5)
        observe_histogram("test_hist", 2.0)

        output = render_prometheus()
        assert "test_hist_count" in output
        assert "test_hist_sum" in output
        assert "test_hist_bucket" in output

        reset_metrics()

    async def test_prometheus_format(self):
        """Render should output valid Prometheus text format."""
        from app.core.metrics import (
            inc_counter,
            observe_histogram,
            render_prometheus,
            reset_metrics,
        )

        reset_metrics()

        inc_counter("http_requests_total", labels={"method": "GET", "status": "200"})
        observe_histogram("http_request_duration_seconds", 0.123)

        output = render_prometheus()
        # Type declarations
        assert "# TYPE http_requests_total counter" in output
        assert "# TYPE http_request_duration_seconds histogram" in output
        # Label format
        assert 'method="GET"' in output
        assert 'status="200"' in output

        reset_metrics()

    async def test_request_id_in_response_header(self, client: AsyncClient):
        """Every response should include X-Request-ID header."""
        resp = await client.get("/health")
        assert "X-Request-ID" in resp.headers
        assert len(resp.headers["X-Request-ID"]) == 8


# ── FM-078: Service-level instrumentation tests ─────────────────


@pytest.mark.asyncio
class TestExecutionServiceMetrics:
    """Verify task lifecycle functions emit metrics."""

    async def test_claim_task_emits_counter(self, db_session):
        """claim_task should increment task_claimed_total."""
        from app.core.metrics import get_counter, reset_metrics
        from app.services import execution_service
        from app.models.project import Project
        from app.models.run import Run
        from app.models.task import Task, TaskStatus
        from app.models.agent import Agent

        reset_metrics()

        # Setup: project -> run -> task + agent
        project = Project(
            name="MetricsProj",
            owner_id=__import__("uuid").UUID("00000000-0000-0000-0000-000000000001"),
        )
        db_session.add(project)
        await db_session.flush()

        run = Run(run_number=1, project_id=project.id, trigger="test")
        db_session.add(run)
        await db_session.flush()

        task = Task(
            title="MetricsTask",
            task_type="code",
            status=TaskStatus.READY,
            order_index=0,
            run_id=run.id,
        )
        db_session.add(task)
        await db_session.flush()

        agent = Agent(name="Test Agent", slug="metric-agent", description="test")
        db_session.add(agent)
        await db_session.flush()
        await db_session.refresh(task)

        await execution_service.claim_task(db_session, task.id, "metric-agent")

        assert (
            get_counter("task_claimed_total", labels={"agent": "metric-agent"}) >= 1.0
        )
        reset_metrics()

    async def test_complete_task_emits_counter(self, db_session):
        """complete_task should increment task_completed_total."""
        from app.core.metrics import get_counter, reset_metrics
        from app.services import execution_service
        from app.models.project import Project
        from app.models.run import Run
        from app.models.task import Task, TaskStatus

        reset_metrics()

        project = Project(
            name="MetricsProj2",
            owner_id=__import__("uuid").UUID("00000000-0000-0000-0000-000000000001"),
        )
        db_session.add(project)
        await db_session.flush()

        run = Run(run_number=1, project_id=project.id, trigger="test")
        db_session.add(run)
        await db_session.flush()

        task = Task(
            title="CompTask",
            task_type="code",
            status=TaskStatus.RUNNING,
            order_index=0,
            run_id=run.id,
            assigned_agent_slug="coder",
        )
        db_session.add(task)
        await db_session.flush()
        await db_session.refresh(task)

        await execution_service.complete_task(db_session, task.id)

        assert get_counter("task_completed_total", labels={"task_type": "code"}) >= 1.0
        reset_metrics()

    async def test_fail_task_emits_counter(self, db_session):
        """fail_task should increment task_failed_total."""
        from app.core.metrics import get_counter, reset_metrics
        from app.services import execution_service
        from app.models.project import Project
        from app.models.run import Run
        from app.models.task import Task, TaskStatus

        reset_metrics()

        project = Project(
            name="MetricsProj3",
            owner_id=__import__("uuid").UUID("00000000-0000-0000-0000-000000000001"),
        )
        db_session.add(project)
        await db_session.flush()

        run = Run(run_number=1, project_id=project.id, trigger="test")
        db_session.add(run)
        await db_session.flush()

        task = Task(
            title="FailTask",
            task_type="code",
            status=TaskStatus.RUNNING,
            order_index=0,
            run_id=run.id,
            assigned_agent_slug="coder",
        )
        db_session.add(task)
        await db_session.flush()
        await db_session.refresh(task)

        await execution_service.fail_task(db_session, task.id, "something broke")

        assert get_counter("task_failed_total") >= 1.0
        reset_metrics()

    async def test_retry_task_emits_counter(self, db_session):
        """retry_task should increment task_retried_total."""
        from app.core.metrics import get_counter, reset_metrics
        from app.services import execution_service
        from app.models.project import Project
        from app.models.run import Run
        from app.models.task import Task, TaskStatus

        reset_metrics()

        project = Project(
            name="MetricsProj4",
            owner_id=__import__("uuid").UUID("00000000-0000-0000-0000-000000000001"),
        )
        db_session.add(project)
        await db_session.flush()

        run = Run(run_number=1, project_id=project.id, trigger="test")
        db_session.add(run)
        await db_session.flush()

        task = Task(
            title="RetryTask",
            task_type="code",
            status=TaskStatus.FAILED,
            order_index=0,
            run_id=run.id,
        )
        db_session.add(task)
        await db_session.flush()
        await db_session.refresh(task)

        await execution_service.retry_task(db_session, task.id)

        assert get_counter("task_retried_total") >= 1.0
        reset_metrics()

    async def test_cancel_task_emits_counter(self, db_session):
        """cancel_task should increment task_cancelled_total."""
        from app.core.metrics import get_counter, reset_metrics
        from app.services import execution_service
        from app.models.project import Project
        from app.models.run import Run
        from app.models.task import Task, TaskStatus

        reset_metrics()

        project = Project(
            name="MetricsProj5",
            owner_id=__import__("uuid").UUID("00000000-0000-0000-0000-000000000001"),
        )
        db_session.add(project)
        await db_session.flush()

        run = Run(run_number=1, project_id=project.id, trigger="test")
        db_session.add(run)
        await db_session.flush()

        task = Task(
            title="CancelTask",
            task_type="code",
            status=TaskStatus.READY,
            order_index=0,
            run_id=run.id,
        )
        db_session.add(task)
        await db_session.flush()
        await db_session.refresh(task)

        await execution_service.cancel_task(db_session, task.id)

        assert get_counter("task_cancelled_total") >= 1.0
        reset_metrics()


@pytest.mark.asyncio
class TestNotificationServiceMetrics:
    """Verify notification functions emit metrics."""

    async def test_create_notification_emits_counter(self, db_session):
        """create_notification should increment notification_created_total."""
        import uuid as _uuid
        from app.core.metrics import get_counter, reset_metrics
        from app.services import notification_service

        reset_metrics()
        user_id = _uuid.UUID("00000000-0000-0000-0000-000000000001")

        await notification_service.create_notification(
            db_session,
            user_id=user_id,
            notification_type="task_completed",
            title="Task done",
            priority="normal",
        )

        assert (
            get_counter(
                "notification_created_total",
                labels={"type": "task_completed", "priority": "normal"},
            )
            >= 1.0
        )
        reset_metrics()

    async def test_mark_notification_read_emits_counter(self, db_session):
        """mark_notification_read should increment notification_read_total."""
        import uuid as _uuid
        from app.core.metrics import get_counter, reset_metrics
        from app.services import notification_service

        reset_metrics()
        user_id = _uuid.UUID("00000000-0000-0000-0000-000000000001")

        n = await notification_service.create_notification(
            db_session,
            user_id=user_id,
            notification_type="system",
            title="Read me",
        )

        await notification_service.mark_notification_read(db_session, n.id)

        assert get_counter("notification_read_total") >= 1.0
        reset_metrics()

    async def test_create_delivery_config_emits_counter(self, db_session):
        """create_delivery_config should increment notification_delivery_config_total."""
        import uuid as _uuid
        from app.core.metrics import get_counter, reset_metrics
        from app.services import notification_service

        reset_metrics()
        user_id = _uuid.UUID("00000000-0000-0000-0000-000000000001")

        await notification_service.create_delivery_config(
            db_session,
            user_id=user_id,
            channel="email",
        )

        assert (
            get_counter(
                "notification_delivery_config_total", labels={"channel": "email"}
            )
            >= 1.0
        )
        reset_metrics()


@pytest.mark.asyncio
class TestSandboxMetrics:
    """Verify sandbox execution functions emit metrics."""

    async def test_create_sandbox_emits_counter(self, db_session, sample_project):
        """create_sandbox_execution should increment sandbox_created_total."""
        from app.core.metrics import get_counter, reset_metrics
        from app.services import code_ops_service

        reset_metrics()

        await code_ops_service.create_sandbox_execution(
            db_session,
            project_id=sample_project.id,
            command="echo hello",
        )

        assert get_counter("sandbox_created_total") >= 1.0
        reset_metrics()

    async def test_complete_sandbox_emits_counter_and_histogram(
        self, db_session, sample_project
    ):
        """complete_sandbox_execution should emit status counter and duration histogram."""
        from app.core.metrics import get_counter, render_prometheus, reset_metrics
        from app.services import code_ops_service
        from app.models.code_ops import SandboxStatus

        reset_metrics()

        sandbox = await code_ops_service.create_sandbox_execution(
            db_session,
            project_id=sample_project.id,
            command="python test.py",
        )

        await code_ops_service.complete_sandbox_execution(
            db_session,
            sandbox.id,
            status=SandboxStatus.COMPLETED,
            exit_code=0,
            duration_ms=1500,
        )

        assert (
            get_counter("sandbox_completed_total", labels={"status": "completed"})
            >= 1.0
        )
        prom = render_prometheus()
        assert "sandbox_duration_seconds" in prom
        reset_metrics()
