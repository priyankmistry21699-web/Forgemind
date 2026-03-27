"""Tests for Connector API endpoints."""

import uuid

import pytest


class TestListConnectors:
    """GET /connectors"""

    async def test_list_connectors(self, client):
        resp = await client.get("/connectors")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        # total may be 0 if no connectors are registered yet
        assert data["total"] >= 0


class TestConnectorRequirements:
    """GET /runs/{run_id}/connectors/requirements"""

    async def test_get_requirements_with_planner_result(
        self, client, sample_run, sample_planner_result
    ):
        resp = await client.get(
            f"/runs/{sample_run.id}/connectors/requirements"
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "recommendations" in data
        assert "total_required" in data
        assert "total_configured" in data

    async def test_get_requirements_no_planner_result(self, client, sample_run):
        """Should still work with an empty planner result (no stack info)."""
        resp = await client.get(
            f"/runs/{sample_run.id}/connectors/requirements"
        )
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data["recommendations"], list)
