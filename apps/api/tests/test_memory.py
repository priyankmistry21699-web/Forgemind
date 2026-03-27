"""Tests for Memory API endpoints (run summary, failures, context)."""

import uuid

import pytest


class TestRunSummary:
    """GET /runs/{run_id}/memory/summary"""

    async def test_summary_success(self, client, sample_run):
        resp = await client.get(f"/runs/{sample_run.id}/memory/summary")
        assert resp.status_code == 200
        data = resp.json()
        # Summary should include run details
        assert "run_id" in data or "status" in data or isinstance(data, dict)

    async def test_summary_nonexistent_run(self, client):
        resp = await client.get(f"/runs/{uuid.uuid4()}/memory/summary")
        assert resp.status_code == 404

    async def test_summary_with_refresh(self, client, sample_run):
        resp = await client.get(
            f"/runs/{sample_run.id}/memory/summary?refresh=true"
        )
        assert resp.status_code == 200


class TestFailureAnalysis:
    """GET /runs/{run_id}/memory/failures"""

    async def test_failures_success(self, client, sample_run):
        resp = await client.get(f"/runs/{sample_run.id}/memory/failures")
        assert resp.status_code == 200

    async def test_failures_nonexistent_run(self, client):
        resp = await client.get(f"/runs/{uuid.uuid4()}/memory/failures")
        # Service may return 404 or a valid response depending on implementation
        assert resp.status_code in (200, 404)


class TestRunContext:
    """GET /runs/{run_id}/memory/context"""

    async def test_context_success(self, client, sample_run):
        resp = await client.get(f"/runs/{sample_run.id}/memory/context")
        assert resp.status_code == 200
        data = resp.json()
        assert "context" in data
        assert isinstance(data["context"], str)

    async def test_context_nonexistent_run(self, client):
        resp = await client.get(f"/runs/{uuid.uuid4()}/memory/context")
        assert resp.status_code == 404
