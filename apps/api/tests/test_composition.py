"""Tests for Composition API endpoints."""

import uuid

import pytest


class TestListCapabilities:
    """GET /composition/capabilities"""

    async def test_list_capabilities(self, client):
        resp = await client.get("/composition/capabilities")
        assert resp.status_code == 200
        data = resp.json()
        assert "capability_groups" in data
        groups = data["capability_groups"]
        assert isinstance(groups, dict)
        assert len(groups) > 0  # Should have at least one capability group


class TestRunComposition:
    """GET /runs/{run_id}/composition"""

    async def test_get_composition(self, client, sample_run, sample_task):
        resp = await client.get(f"/runs/{sample_run.id}/composition")
        assert resp.status_code == 200
        data = resp.json()
        assert "required_capabilities" in data
        assert "assignments" in data
        assert "coverage" in data
        assert "gaps" in data
        assert "agent_count" in data
        assert isinstance(data["coverage"], (int, float))
        assert 0.0 <= data["coverage"] <= 1.0

    async def test_get_composition_empty_run(self, client, sample_run):
        """A run with no tasks should still return a valid composition."""
        resp = await client.get(f"/runs/{sample_run.id}/composition")
        assert resp.status_code == 200
        data = resp.json()
        assert data["agent_count"] >= 0
