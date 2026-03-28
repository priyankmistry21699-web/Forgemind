"""Tests for membership endpoints (FM-052, FM-053)."""
import uuid
import pytest
from httpx import AsyncClient

STUB_USER_ID = "00000000-0000-0000-0000-000000000001"


@pytest.mark.asyncio
class TestWorkspaceMembers:

    async def _make_workspace(self, client: AsyncClient, slug: str) -> str:
        resp = await client.post("/workspaces", json={"name": "WS", "slug": slug})
        return resp.json()["id"]

    async def test_add_member(self, client: AsyncClient):
        ws_id = await self._make_workspace(client, "mem-add")
        resp = await client.post(f"/workspaces/{ws_id}/members", json={
            "user_id": STUB_USER_ID, "role": "admin",
        })
        assert resp.status_code == 201
        assert resp.json()["role"] == "admin"

    async def test_add_duplicate_member(self, client: AsyncClient):
        ws_id = await self._make_workspace(client, "mem-dup")
        await client.post(f"/workspaces/{ws_id}/members", json={
            "user_id": STUB_USER_ID, "role": "viewer",
        })
        resp = await client.post(f"/workspaces/{ws_id}/members", json={
            "user_id": STUB_USER_ID, "role": "admin",
        })
        assert resp.status_code == 409

    async def test_list_members(self, client: AsyncClient):
        ws_id = await self._make_workspace(client, "mem-list")
        await client.post(f"/workspaces/{ws_id}/members", json={
            "user_id": STUB_USER_ID, "role": "viewer",
        })
        resp = await client.get(f"/workspaces/{ws_id}/members")
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    async def test_update_member_role(self, client: AsyncClient):
        ws_id = await self._make_workspace(client, "mem-upd")
        await client.post(f"/workspaces/{ws_id}/members", json={
            "user_id": STUB_USER_ID, "role": "viewer",
        })
        resp = await client.patch(
            f"/workspaces/{ws_id}/members/{STUB_USER_ID}",
            json={"role": "operator"},
        )
        assert resp.status_code == 200
        assert resp.json()["role"] == "operator"

    async def test_remove_member(self, client: AsyncClient):
        ws_id = await self._make_workspace(client, "mem-rm")
        await client.post(f"/workspaces/{ws_id}/members", json={
            "user_id": STUB_USER_ID, "role": "viewer",
        })
        resp = await client.delete(f"/workspaces/{ws_id}/members/{STUB_USER_ID}")
        assert resp.status_code == 204

    async def test_remove_member_404(self, client: AsyncClient):
        ws_id = await self._make_workspace(client, "mem-rm404")
        resp = await client.delete(f"/workspaces/{ws_id}/members/{uuid.uuid4()}")
        assert resp.status_code == 404


@pytest.mark.asyncio
class TestProjectMembers:

    async def test_add_project_member(self, client: AsyncClient, sample_project):
        pid = str(sample_project.id)
        resp = await client.post(f"/projects/{pid}/members", json={
            "user_id": STUB_USER_ID, "role": "lead", "is_approver": True,
        })
        assert resp.status_code == 201
        assert resp.json()["is_approver"] is True

    async def test_list_project_members(self, client: AsyncClient, sample_project):
        pid = str(sample_project.id)
        await client.post(f"/projects/{pid}/members", json={
            "user_id": STUB_USER_ID,
        })
        resp = await client.get(f"/projects/{pid}/members")
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    async def test_update_project_member(self, client: AsyncClient, sample_project):
        pid = str(sample_project.id)
        await client.post(f"/projects/{pid}/members", json={
            "user_id": STUB_USER_ID,
        })
        resp = await client.patch(
            f"/projects/{pid}/members/{STUB_USER_ID}",
            json={"role": "operator", "is_reviewer": True},
        )
        assert resp.status_code == 200
        assert resp.json()["role"] == "operator"
        assert resp.json()["is_reviewer"] is True

    async def test_remove_project_member(self, client: AsyncClient, sample_project):
        pid = str(sample_project.id)
        await client.post(f"/projects/{pid}/members", json={
            "user_id": STUB_USER_ID,
        })
        resp = await client.delete(f"/projects/{pid}/members/{STUB_USER_ID}")
        assert resp.status_code == 204
