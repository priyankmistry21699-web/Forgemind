"""Tests for notification endpoints (FM-055, FM-056)."""
import uuid
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestNotifications:

    async def test_create_notification(self, client: AsyncClient):
        resp = await client.post("/notifications", json={
            "notification_type": "task_assigned",
            "title": "You have a new task",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "You have a new task"
        assert data["is_read"] is False

    async def test_list_notifications(self, client: AsyncClient):
        await client.post("/notifications", json={
            "notification_type": "system", "title": "Test",
        })
        resp = await client.get("/notifications")
        assert resp.status_code == 200
        data = resp.json()
        assert "unread_count" in data
        assert data["total"] >= 1

    async def test_list_unread_only(self, client: AsyncClient):
        await client.post("/notifications", json={
            "notification_type": "system", "title": "Unread",
        })
        resp = await client.get("/notifications?unread_only=true")
        assert resp.status_code == 200
        for item in resp.json()["items"]:
            assert item["is_read"] is False

    async def test_mark_read(self, client: AsyncClient):
        create = await client.post("/notifications", json={
            "notification_type": "system", "title": "Mark me",
        })
        nid = create.json()["id"]
        resp = await client.post(f"/notifications/{nid}/read")
        assert resp.status_code == 200
        assert resp.json()["is_read"] is True

    async def test_mark_read_404(self, client: AsyncClient):
        resp = await client.post(f"/notifications/{uuid.uuid4()}/read")
        assert resp.status_code == 404

    async def test_mark_all_read(self, client: AsyncClient):
        await client.post("/notifications", json={
            "notification_type": "system", "title": "A",
        })
        resp = await client.post("/notifications/read-all")
        assert resp.status_code == 200
        assert "marked" in resp.json()


@pytest.mark.asyncio
class TestDeliveryConfig:

    async def test_create_config(self, client: AsyncClient):
        resp = await client.post("/notifications/delivery", json={
            "channel": "slack",
        })
        assert resp.status_code == 201
        assert resp.json()["channel"] == "slack"

    async def test_list_configs(self, client: AsyncClient):
        await client.post("/notifications/delivery", json={
            "channel": "email",
        })
        resp = await client.get("/notifications/delivery")
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1
