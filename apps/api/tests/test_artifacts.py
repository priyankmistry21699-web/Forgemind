"""Tests for Artifact API endpoints."""

import uuid

import pytest


class TestCreateArtifact:
    """POST /projects/{project_id}/artifacts"""

    async def test_create_artifact_success(self, client, sample_project, sample_run):
        resp = await client.post(
            f"/projects/{sample_project.id}/artifacts",
            json={
                "title": "Architecture Design",
                "artifact_type": "architecture",
                "content": "# System Architecture\nMicroservices with API gateway.",
                "run_id": str(sample_run.id),
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "Architecture Design"
        assert data["artifact_type"] == "architecture"
        assert data["version"] == 1

    async def test_create_artifact_minimal(self, client, sample_project):
        resp = await client.post(
            f"/projects/{sample_project.id}/artifacts",
            json={"title": "Quick Note"},
        )
        assert resp.status_code == 201
        assert resp.json()["artifact_type"] == "other"

    async def test_create_artifact_empty_title_fails(self, client, sample_project):
        resp = await client.post(
            f"/projects/{sample_project.id}/artifacts",
            json={"title": ""},
        )
        assert resp.status_code == 422


class TestListArtifacts:
    """GET /projects/{project_id}/artifacts"""

    async def test_list_artifacts(self, client, sample_project, sample_artifact):
        resp = await client.get(f"/projects/{sample_project.id}/artifacts")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1

    async def test_list_artifacts_filter_by_run(
        self, client, sample_project, sample_run, sample_artifact
    ):
        resp = await client.get(
            f"/projects/{sample_project.id}/artifacts?run_id={sample_run.id}"
        )
        assert resp.status_code == 200
        data = resp.json()
        assert all(a["run_id"] == str(sample_run.id) for a in data["items"])


class TestGetArtifact:
    """GET /artifacts/{artifact_id}"""

    async def test_get_artifact_success(self, client, sample_artifact):
        resp = await client.get(f"/artifacts/{sample_artifact.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "Test Artifact"
        assert data["content"] == "# Architecture\nTest content"

    async def test_get_artifact_not_found(self, client):
        resp = await client.get(f"/artifacts/{uuid.uuid4()}")
        assert resp.status_code == 404


class TestUpdateArtifact:
    """PATCH /artifacts/{artifact_id}"""

    async def test_update_artifact_content(self, client, sample_artifact):
        resp = await client.patch(
            f"/artifacts/{sample_artifact.id}",
            json={"content": "Updated architecture document"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["content"] == "Updated architecture document"
        # Version should be bumped on content change
        assert data["version"] >= 1

    async def test_update_artifact_title(self, client, sample_artifact):
        resp = await client.patch(
            f"/artifacts/{sample_artifact.id}",
            json={"title": "Updated Title"},
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "Updated Title"


class TestDeleteArtifact:
    """DELETE /artifacts/{artifact_id}"""

    async def test_delete_artifact(self, client, sample_artifact):
        resp = await client.delete(f"/artifacts/{sample_artifact.id}")
        assert resp.status_code == 204

        # Verify it's gone
        resp = await client.get(f"/artifacts/{sample_artifact.id}")
        assert resp.status_code == 404

    async def test_delete_artifact_not_found(self, client):
        resp = await client.delete(f"/artifacts/{uuid.uuid4()}")
        assert resp.status_code == 404
