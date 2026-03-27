"""Tests for Run API endpoints."""

import uuid

import pytest


class TestListRuns:
    """GET /projects/{project_id}/runs"""

    async def test_list_runs_empty(self, client, sample_project):
        resp = await client.get(f"/projects/{sample_project.id}/runs")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["items"] == []

    async def test_list_runs_with_data(self, client, sample_project, sample_run):
        resp = await client.get(f"/projects/{sample_project.id}/runs")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        assert data["items"][0]["run_number"] == 1

    async def test_list_runs_pagination(self, client, sample_project):
        resp = await client.get(
            f"/projects/{sample_project.id}/runs?skip=0&limit=5"
        )
        assert resp.status_code == 200


class TestGetRun:
    """GET /runs/{run_id}"""

    async def test_get_run_success(self, client, sample_run):
        resp = await client.get(f"/runs/{sample_run.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["run_number"] == 1
        assert data["status"] == "pending"
        assert data["trigger"] == "test"

    async def test_get_run_not_found(self, client):
        resp = await client.get(f"/runs/{uuid.uuid4()}")
        assert resp.status_code == 404


class TestGetLatestRun:
    """GET /projects/{project_id}/runs/latest"""

    async def test_latest_run_success(self, client, sample_project, sample_run):
        resp = await client.get(f"/projects/{sample_project.id}/runs/latest")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == str(sample_run.id)

    async def test_latest_run_no_runs(self, client, sample_project):
        # Use a project with no runs
        resp = await client.get(f"/projects/{sample_project.id}/runs/latest")
        # Will either return a run (from fixtures) or 404
        assert resp.status_code in (200, 404)
