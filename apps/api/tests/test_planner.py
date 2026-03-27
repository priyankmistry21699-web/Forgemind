"""Tests for Planner & Planner Results API endpoints."""

import uuid
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone

import pytest


def _make_mock_planner_response(project_name="Blog API"):
    """Create mock objects for planner response."""
    project = MagicMock()
    project.id = uuid.uuid4()
    project.created_at = datetime.now(timezone.utc)

    run = MagicMock()
    run.id = uuid.uuid4()

    tasks = [MagicMock() for _ in range(3)]

    planner_result = MagicMock()
    planner_result.overview = "Stub planning result"

    return project, run, tasks, planner_result


class TestPromptIntake:
    """POST /planner/intake"""

    async def test_prompt_intake_stub(self, client):
        """Without LLM API keys, the planner uses a stub path."""
        mock_result = _make_mock_planner_response()
        with patch(
            "app.api.routes.planner.plan_from_prompt",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            resp = await client.post(
                "/planner/intake",
                json={
                    "prompt": "Build a REST API for a blog with users, posts, and comments.",
                    "project_name": "Blog API",
                },
            )
            assert resp.status_code == 201
            data = resp.json()
            assert "project_id" in data
            assert "run_id" in data
            assert data["tasks_created"] == 3
            assert "stub" in data["message"].lower()

    async def test_prompt_intake_auto_name(self, client):
        """When project_name is omitted, planner auto-generates one."""
        mock_result = _make_mock_planner_response()
        with patch(
            "app.api.routes.planner.plan_from_prompt",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            resp = await client.post(
                "/planner/intake",
                json={
                    "prompt": "Build a mobile app for tracking fitness goals.",
                },
            )
            assert resp.status_code == 201
            data = resp.json()
            assert data["tasks_created"] == 3

    async def test_prompt_intake_short_prompt(self, client):
        """Prompt too short should be rejected by schema validation."""
        resp = await client.post(
            "/planner/intake",
            json={"prompt": "Hi"},
        )
        assert resp.status_code == 422


class TestGetPlannerResult:
    """GET /runs/{run_id}/plan"""

    async def test_get_planner_result_success(
        self, client, sample_run, sample_planner_result
    ):
        resp = await client.get(f"/runs/{sample_run.id}/plan")
        assert resp.status_code == 200
        data = resp.json()
        assert data["overview"] == "Test planner overview — build an API"
        assert "Python" in data["recommended_stack"].values()

    async def test_get_planner_result_not_found(self, client):
        """Run ID with no planner result should 404."""
        # Use a random UUID that doesn't have a planner result
        resp = await client.get(f"/runs/{uuid.uuid4()}/plan")
        assert resp.status_code == 404

    async def test_get_planner_result_invalid_run(self, client):
        resp = await client.get(f"/runs/{uuid.uuid4()}/plan")
        assert resp.status_code == 404
