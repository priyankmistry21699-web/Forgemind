"""Tests for workspace endpoints (FM-051)."""
import uuid
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestWorkspaces:

    async def test_create_workspace(self, client: AsyncClient):
        resp = await client.post("/workspaces", json={
            "name": "Acme Corp", "slug": "acme-corp",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Acme Corp"
        assert data["slug"] == "acme-corp"
        assert data["status"] == "active"

    async def test_create_duplicate_slug(self, client: AsyncClient):
        await client.post("/workspaces", json={"name": "WS", "slug": "dup"})
        resp = await client.post("/workspaces", json={"name": "WS2", "slug": "dup"})
        assert resp.status_code == 409

    async def test_list_workspaces(self, client: AsyncClient):
        await client.post("/workspaces", json={"name": "WS1", "slug": "ws-list-1"})
        resp = await client.get("/workspaces")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        assert len(data["items"]) >= 1

    async def test_get_workspace(self, client: AsyncClient):
        create = await client.post("/workspaces", json={"name": "G", "slug": "get-ws"})
        ws_id = create.json()["id"]
        resp = await client.get(f"/workspaces/{ws_id}")
        assert resp.status_code == 200
        assert resp.json()["slug"] == "get-ws"

    async def test_get_workspace_404(self, client: AsyncClient):
        resp = await client.get(f"/workspaces/{uuid.uuid4()}")
        assert resp.status_code == 404

    async def test_update_workspace(self, client: AsyncClient):
        create = await client.post("/workspaces", json={"name": "Old", "slug": "upd-ws"})
        ws_id = create.json()["id"]
        resp = await client.patch(f"/workspaces/{ws_id}", json={"name": "New"})
        assert resp.status_code == 200
        assert resp.json()["name"] == "New"

    async def test_delete_workspace(self, client: AsyncClient):
        create = await client.post("/workspaces", json={"name": "D", "slug": "del-ws"})
        ws_id = create.json()["id"]
        resp = await client.delete(f"/workspaces/{ws_id}")
        assert resp.status_code == 204
        resp2 = await client.get(f"/workspaces/{ws_id}")
        assert resp2.status_code == 404

    async def test_delete_workspace_404(self, client: AsyncClient):
        resp = await client.delete(f"/workspaces/{uuid.uuid4()}")
        assert resp.status_code == 404
