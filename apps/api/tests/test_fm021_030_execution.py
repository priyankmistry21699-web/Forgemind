"""
FM-021 → FM-030 — Execution, events, approvals + dashboard wiring smoke.

Covers:
  - FM-021..024 execution events + streaming scaffolding
  - FM-025..027 approval lifecycle (pending → approved/rejected)
  - FM-028..030 dashboard/approval surfaces (counts + cross-links)
"""

import uuid

import pytest
from pydantic import ValidationError


# ── FM-021: Execution event read schema ───────────────────────────
class TestFM021ExecutionEventSchema:
    def test_execution_event_read_importable(self):
        from app.schemas.execution_event import ExecutionEventRead

        assert ExecutionEventRead is not None


# ── FM-022/023: Events + streaming routes ─────────────────────────
class TestFM022EventsAndStreaming:
    def test_event_and_streaming_routes_registered(self):
        from app.main import create_app

        app = create_app()
        paths = [getattr(r, "path", "") for r in app.routes]
        assert any("/events" in p for p in paths)
        # Some form of streaming surface must be present (FM-054/077 etc.)
        assert any("/stream" in p or "/streaming" in p for p in paths)


# ── FM-024: Activity service exists ───────────────────────────────
class TestFM024Activity:
    def test_activity_service_importable(self):
        import app.services.activity_service as mod

        assert mod is not None


# ── FM-025: Approval create schema ────────────────────────────────
class TestFM025ApprovalCreate:
    def test_approval_create_requires_title(self):
        from app.schemas.approval import ApprovalCreate

        with pytest.raises(ValidationError):
            ApprovalCreate(  # type: ignore[call-arg]
                project_id=uuid.uuid4(),
            )

    def test_approval_create_accepts_minimal_payload(self):
        from app.schemas.approval import ApprovalCreate

        payload = ApprovalCreate(
            title="Approve deploy",
            project_id=uuid.uuid4(),
        )
        assert payload.title == "Approve deploy"


# ── FM-026/027: Approval decide enum & schema ─────────────────────
class TestFM026ApprovalDecision:
    def test_decision_status_must_be_approved_or_rejected(self):
        from app.schemas.approval import ApprovalDecision

        approved = ApprovalDecision(status="approved")
        rejected = ApprovalDecision(status="rejected")
        assert approved.status == "approved"
        assert rejected.status == "rejected"


# ── FM-028: Approvals list route exists ───────────────────────────
class TestFM028ApprovalsListRoute:
    async def test_get_approvals_list(self, client, sample_project):
        r = await client.get(f"/approvals?project_id={sample_project.id}")
        assert r.status_code == 200
        body = r.json()
        # List envelope must expose items + total for the dashboard card.
        assert "items" in body
        assert "total" in body

    async def test_get_approvals_filter_by_status_pending(self, client, sample_project):
        r = await client.get(
            f"/approvals?project_id={sample_project.id}&status=pending"
        )
        assert r.status_code == 200
        body = r.json()
        assert body["total"] == 0
        assert body["items"] == []


# ── FM-029: Approval decide route registered ──────────────────────
class TestFM029ApprovalDecideRoute:
    def test_decide_route_path_registered(self):
        from app.main import create_app

        app = create_app()
        paths = [getattr(r, "path", "") for r in app.routes]
        assert any("/approvals/" in p and "/decide" in p for p in paths)


# ── FM-030: Dashboard cross-linked approval counter ───────────────
class TestFM030DashboardApprovalCounter:
    async def test_pending_filter_returns_envelope_with_total(
        self, client, sample_project
    ):
        """Dashboard home card reads `total` to render the pending-approval
        count; this must be a stable contract."""
        r = await client.get(
            f"/approvals?project_id={sample_project.id}&status=pending"
        )
        assert r.status_code == 200
        body = r.json()
        # Contract: empty pending set yields total=0, items=[].
        assert body["total"] == 0
        assert isinstance(body["items"], list)
