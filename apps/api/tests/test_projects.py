"""Tests for Project CRUD API endpoints."""

import uuid

import pytest


class TestCreateProject:
    """POST /projects"""

    async def test_create_project_success(self, client):
        resp = await client.post(
            "/projects",
            json={"name": "New Project", "description": "Test description"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "New Project"
        assert data["description"] == "Test description"
        assert data["status"] == "draft"
        assert "id" in data
        assert "created_at" in data

    async def test_create_project_minimal(self, client):
        resp = await client.post("/projects", json={"name": "Minimal"})
        assert resp.status_code == 201
        assert resp.json()["description"] is None

    async def test_create_project_empty_name_fails(self, client):
        resp = await client.post("/projects", json={"name": ""})
        assert resp.status_code == 422

    async def test_create_project_missing_name_fails(self, client):
        resp = await client.post("/projects", json={})
        assert resp.status_code == 422


class TestListProjects:
    """GET /projects"""

    async def test_list_projects_empty(self, client):
        resp = await client.get("/projects")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)

    async def test_list_projects_with_data(self, client, sample_project):
        resp = await client.get("/projects")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        assert any(p["name"] == "Test Project" for p in data["items"])

    async def test_list_projects_pagination(self, client):
        # Create 3 projects
        for i in range(3):
            await client.post("/projects", json={"name": f"Project {i}"})

        resp = await client.get("/projects?skip=0&limit=2")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) <= 2

    async def test_list_projects_invalid_limit(self, client):
        resp = await client.get("/projects?limit=0")
        assert resp.status_code == 422

    async def test_list_projects_invalid_skip(self, client):
        resp = await client.get("/projects?skip=-1")
        assert resp.status_code == 422


class TestGetProject:
    """GET /projects/{project_id}"""

    async def test_get_project_success(self, client, sample_project):
        resp = await client.get(f"/projects/{sample_project.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Test Project"
        assert data["id"] == str(sample_project.id)

    async def test_get_project_not_found(self, client):
        fake_id = uuid.uuid4()
        resp = await client.get(f"/projects/{fake_id}")
        assert resp.status_code == 404


class TestUpdateProject:
    """PATCH /projects/{project_id}"""

    async def test_update_project_name(self, client, sample_project):
        resp = await client.patch(
            f"/projects/{sample_project.id}",
            json={"name": "Updated Name"},
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Updated Name"

    async def test_update_project_status(self, client, sample_project):
        resp = await client.patch(
            f"/projects/{sample_project.id}",
            json={"status": "active"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "active"

    async def test_update_project_not_found(self, client):
        fake_id = uuid.uuid4()
        resp = await client.patch(
            f"/projects/{fake_id}",
            json={"name": "Won't work"},
        )
        assert resp.status_code == 404
