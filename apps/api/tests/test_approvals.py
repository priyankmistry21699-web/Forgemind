"""Tests for Approval API endpoints."""

import uuid

import pytest


class TestListApprovals:
    """GET /approvals"""

    async def test_list_approvals_empty(self, client):
        resp = await client.get("/approvals")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["items"] == []

    async def test_list_approvals_with_data(self, client, sample_approval):
        resp = await client.get("/approvals")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        assert data["items"][0]["status"] == "pending"

    async def test_list_approvals_filter_by_status(self, client, sample_approval):
        resp = await client.get("/approvals?status=pending")
        assert resp.status_code == 200
        data = resp.json()
        assert all(a["status"] == "pending" for a in data["items"])

    async def test_list_approvals_filter_by_project(
        self, client, sample_project, sample_approval
    ):
        resp = await client.get(f"/approvals?project_id={sample_project.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1


class TestGetApproval:
    """GET /approvals/{approval_id}"""

    async def test_get_approval_success(self, client, sample_approval):
        resp = await client.get(f"/approvals/{sample_approval.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "Approve architecture"
        assert data["status"] == "pending"

    async def test_get_approval_not_found(self, client):
        resp = await client.get(f"/approvals/{uuid.uuid4()}")
        assert resp.status_code == 404


class TestDecideApproval:
    """POST /approvals/{approval_id}/decide"""

    async def test_approve(self, client, sample_approval):
        resp = await client.post(
            f"/approvals/{sample_approval.id}/decide",
            json={
                "status": "approved",
                "decision_comment": "Looks good to proceed.",
                "decided_by": "reviewer@forgemind.dev",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "approved"

    async def test_reject(self, client, sample_approval):
        resp = await client.post(
            f"/approvals/{sample_approval.id}/decide",
            json={
                "status": "rejected",
                "decision_comment": "Needs rework.",
                "decided_by": "reviewer@forgemind.dev",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "rejected"
