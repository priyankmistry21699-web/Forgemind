"""Tests for escalation endpoints (FM-057)."""
import uuid
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestEscalationRules:

    async def test_create_rule(self, client: AsyncClient, sample_project):
        pid = str(sample_project.id)
        resp = await client.post(f"/projects/{pid}/escalation/rules", json={
            "name": "Task Timeout",
            "trigger": "task_timeout",
            "action": "notify",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Task Timeout"
        assert data["cooldown_minutes"] == 30

    async def test_list_rules(self, client: AsyncClient, sample_project):
        pid = str(sample_project.id)
        await client.post(f"/projects/{pid}/escalation/rules", json={
            "name": "R1", "trigger": "run_failure", "action": "pause_run",
        })
        resp = await client.get(f"/projects/{pid}/escalation/rules")
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    async def test_get_rule(self, client: AsyncClient, sample_project):
        pid = str(sample_project.id)
        create = await client.post(f"/projects/{pid}/escalation/rules", json={
            "name": "R", "trigger": "custom", "action": "reassign",
        })
        rid = create.json()["id"]
        resp = await client.get(f"/escalation/rules/{rid}")
        assert resp.status_code == 200

    async def test_get_rule_404(self, client: AsyncClient):
        resp = await client.get(f"/escalation/rules/{uuid.uuid4()}")
        assert resp.status_code == 404

    async def test_update_rule(self, client: AsyncClient, sample_project):
        pid = str(sample_project.id)
        create = await client.post(f"/projects/{pid}/escalation/rules", json={
            "name": "Upd", "trigger": "custom", "action": "notify",
        })
        rid = create.json()["id"]
        resp = await client.patch(f"/escalation/rules/{rid}", json={
            "name": "Updated",
        })
        assert resp.status_code == 200
        assert resp.json()["name"] == "Updated"

    async def test_delete_rule(self, client: AsyncClient, sample_project):
        pid = str(sample_project.id)
        create = await client.post(f"/projects/{pid}/escalation/rules", json={
            "name": "Del", "trigger": "custom", "action": "auto_cancel",
        })
        rid = create.json()["id"]
        resp = await client.delete(f"/escalation/rules/{rid}")
        assert resp.status_code == 204

    async def test_delete_rule_404(self, client: AsyncClient):
        resp = await client.delete(f"/escalation/rules/{uuid.uuid4()}")
        assert resp.status_code == 404

    async def test_events_empty(self, client: AsyncClient, sample_project):
        pid = str(sample_project.id)
        resp = await client.get(f"/projects/{pid}/escalation/events")
        assert resp.status_code == 200
        assert resp.json()["total"] == 0
