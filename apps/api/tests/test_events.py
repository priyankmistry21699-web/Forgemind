"""Tests for Execution Event API endpoints."""

import uuid

import pytest


class TestListEvents:
    """GET /events"""

    async def test_list_events_empty(self, client):
        resp = await client.get("/events")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["items"] == []

    async def test_list_events_filter_by_run(self, client, sample_run):
        resp = await client.get(f"/events?run_id={sample_run.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 0

    async def test_list_events_filter_by_project(self, client, sample_project):
        resp = await client.get(f"/events?project_id={sample_project.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 0

    async def test_list_events_pagination(self, client):
        resp = await client.get("/events?limit=10&offset=0")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
