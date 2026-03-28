"""Tests for activity and presence endpoints (FM-058, FM-059)."""
import uuid
import pytest
from httpx import AsyncClient

STUB_USER_ID = "00000000-0000-0000-0000-000000000001"


@pytest.mark.asyncio
class TestActivityFeed:

    async def test_create_activity(self, client: AsyncClient):
        resp = await client.post("/activity", json={
            "activity_type": "project_created",
            "summary": "Created project Alpha",
        })
        assert resp.status_code == 201
        assert resp.json()["summary"] == "Created project Alpha"

    async def test_list_activities(self, client: AsyncClient):
        await client.post("/activity", json={
            "activity_type": "comment", "summary": "Hello",
        })
        resp = await client.get("/activity")
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    async def test_list_by_project(self, client: AsyncClient, sample_project):
        pid = str(sample_project.id)
        await client.post("/activity", json={
            "activity_type": "run_started", "summary": "Run 1",
            "project_id": pid,
        })
        resp = await client.get(f"/activity?project_id={pid}")
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1


@pytest.mark.asyncio
class TestPresence:

    async def test_update_presence(self, client: AsyncClient):
        resp = await client.put("/presence", json={"status": "online"})
        assert resp.status_code == 200
        assert resp.json()["status"] == "online"

    async def test_update_presence_with_resource(self, client: AsyncClient):
        resp = await client.put("/presence", json={
            "status": "busy",
            "current_resource_type": "project",
            "current_resource_id": str(uuid.uuid4()),
        })
        assert resp.status_code == 200
        assert resp.json()["status"] == "busy"

    async def test_get_presence(self, client: AsyncClient):
        await client.put("/presence", json={"status": "online"})
        resp = await client.get(f"/presence/{STUB_USER_ID}")
        assert resp.status_code == 200

    async def test_get_presence_404(self, client: AsyncClient):
        resp = await client.get(f"/presence/{uuid.uuid4()}")
        assert resp.status_code == 404

    async def test_list_presence(self, client: AsyncClient):
        await client.put("/presence", json={"status": "online"})
        resp = await client.get("/presence")
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1
