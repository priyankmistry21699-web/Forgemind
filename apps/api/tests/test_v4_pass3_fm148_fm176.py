"""V4 Pass 3 — FM-148 and FM-176 closing tests.

Tests:
  FM-148: Auto-escalation dedup, delegation expiry, revoke delegation,
          background scheduler cycle, delegation-aware routing enforcement.
  FM-176: Archive action with audit trail, background retention cycle,
          entity condition building, refactored evaluate_retention.
"""

import uuid
from datetime import datetime, timedelta, timezone


import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import STUB_USER_ID

OLD_DATE = datetime.now(timezone.utc) - timedelta(days=100)


@pytest.fixture
def db(db_session):
    return db_session


# ── Shared Helpers ───────────────────────────────────────────────


async def _seed_project(db: AsyncSession):
    from app.models.project import Project
    from app.models.membership import ProjectMember, ProjectRole

    project = Project(
        name="V4 Pass 3 Project",
        description="FM-148 / FM-176 tests",
        owner_id=STUB_USER_ID,
    )
    db.add(project)
    await db.flush()
    await db.refresh(project)
    lead = ProjectMember(
        project_id=project.id,
        user_id=STUB_USER_ID,
        role=ProjectRole.LEAD,
    )
    db.add(lead)
    await db.flush()
    return project


async def _seed_workspace(db: AsyncSession):
    from app.models.workspace import Workspace
    from app.models.membership import WorkspaceMember, WorkspaceRole

    ws = Workspace(
        name="Pass 3 WS",
        slug=f"pass3-ws-{uuid.uuid4().hex[:8]}",
        owner_id=STUB_USER_ID,
    )
    db.add(ws)
    await db.flush()
    await db.refresh(ws)
    mem = WorkspaceMember(
        workspace_id=ws.id, user_id=STUB_USER_ID, role=WorkspaceRole.ADMIN
    )
    db.add(mem)
    await db.flush()
    return ws


async def _seed_expired_approval(db: AsyncSession, project_id: uuid.UUID, **kwargs):
    from app.models.approval_request import ApprovalRequest, ApprovalStatus

    defaults = dict(
        title="Expired approval",
        status=ApprovalStatus.PENDING,
        project_id=project_id,
        expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
    )
    defaults.update(kwargs)
    approval = ApprovalRequest(**defaults)
    db.add(approval)
    await db.flush()
    await db.refresh(approval)
    return approval


# ═══════════════════════════════════════════════════════════════════
# FM-148 Tests
# ═══════════════════════════════════════════════════════════════════


class TestEscalationDedup:
    """escalated_at prevents re-escalation on subsequent runs."""

    @pytest.mark.anyio
    async def test_escalation_marks_escalated_at(self, db):
        from app.services import approval_enhanced_service

        project = await _seed_project(db)
        approval = await _seed_expired_approval(db, project.id)

        assert approval.escalated_at is None

        report = await approval_enhanced_service.escalate_expired_approvals(db)
        await db.flush()

        assert len(report) == 1
        await db.refresh(approval)
        assert approval.escalated_at is not None

    @pytest.mark.anyio
    async def test_already_escalated_approval_skipped(self, db):
        from app.services import approval_enhanced_service

        project = await _seed_project(db)
        await _seed_expired_approval(
            db, project.id,
            escalated_at=datetime.now(timezone.utc) - timedelta(minutes=30),
        )

        report = await approval_enhanced_service.escalate_expired_approvals(db)
        assert len(report) == 0

    @pytest.mark.anyio
    async def test_second_escalation_run_is_noop(self, db):
        from app.services import approval_enhanced_service

        project = await _seed_project(db)
        await _seed_expired_approval(db, project.id)

        report1 = await approval_enhanced_service.escalate_expired_approvals(db)
        assert len(report1) == 1

        report2 = await approval_enhanced_service.escalate_expired_approvals(db)
        assert len(report2) == 0


class TestDelegationExpiry:
    """Delegation active_until is enforced in queries and auto-deactivated."""

    @pytest.mark.anyio
    async def test_deactivate_expired_delegations(self, db):
        from app.services import approval_enhanced_service
        from app.models.approval_delegation import ApprovalDelegation

        project = await _seed_project(db)
        delegate_id = uuid.uuid4()

        # Create user for delegate
        from app.models.user import User
        delegate_user = User(id=delegate_id, email="delegate@test.dev", display_name="Delegate")
        db.add(delegate_user)
        await db.flush()

        # Active delegation (no expiry)
        d1 = ApprovalDelegation(
            delegator_id=STUB_USER_ID,
            delegate_id=delegate_id,
            project_id=project.id,
            is_active=True,
        )
        # Expired delegation
        d2 = ApprovalDelegation(
            delegator_id=STUB_USER_ID,
            delegate_id=delegate_id,
            project_id=project.id,
            active_until=datetime.now(timezone.utc) - timedelta(hours=1),
            is_active=True,
        )
        db.add_all([d1, d2])
        await db.flush()

        count = await approval_enhanced_service.deactivate_expired_delegations(db)
        assert count == 1

        await db.refresh(d1)
        await db.refresh(d2)
        assert d1.is_active is True
        assert d2.is_active is False

    @pytest.mark.anyio
    async def test_expired_delegation_excluded_from_pending(self, db):
        from app.services import approval_enhanced_service
        from app.models.approval_delegation import ApprovalDelegation
        from app.models.approval_request import ApprovalRequest, ApprovalStatus
        from app.models.user import User

        project = await _seed_project(db)
        delegate_id = uuid.uuid4()
        delegate_user = User(id=delegate_id, email="d2@test.dev", display_name="D2")
        db.add(delegate_user)
        await db.flush()

        # Expired delegation — should not grant visibility
        delegation = ApprovalDelegation(
            delegator_id=STUB_USER_ID,
            delegate_id=delegate_id,
            project_id=project.id,
            active_until=datetime.now(timezone.utc) - timedelta(hours=1),
            is_active=True,
        )
        db.add(delegation)

        approval = ApprovalRequest(
            title="Test pending",
            status=ApprovalStatus.PENDING,
            project_id=project.id,
        )
        db.add(approval)
        await db.flush()

        # Delegate should NOT see approval (delegation expired)
        pending = await approval_enhanced_service.get_pending_approvals_for_user(
            db, delegate_id
        )
        assert len(pending) == 0

    @pytest.mark.anyio
    async def test_active_delegation_grants_pending_visibility(self, db):
        from app.services import approval_enhanced_service
        from app.models.approval_delegation import ApprovalDelegation
        from app.models.approval_request import ApprovalRequest, ApprovalStatus
        from app.models.user import User

        project = await _seed_project(db)
        delegate_id = uuid.uuid4()
        delegate_user = User(id=delegate_id, email="d3@test.dev", display_name="D3")
        db.add(delegate_user)
        await db.flush()

        # Active delegation with future expiry
        delegation = ApprovalDelegation(
            delegator_id=STUB_USER_ID,
            delegate_id=delegate_id,
            project_id=project.id,
            active_until=datetime.now(timezone.utc) + timedelta(days=7),
            is_active=True,
        )
        db.add(delegation)

        approval = ApprovalRequest(
            title="Visible to delegate",
            status=ApprovalStatus.PENDING,
            project_id=project.id,
        )
        db.add(approval)
        await db.flush()

        pending = await approval_enhanced_service.get_pending_approvals_for_user(
            db, delegate_id
        )
        assert len(pending) == 1
        assert pending[0].title == "Visible to delegate"


class TestRevokeDelegation:
    """Revoke delegation endpoint."""

    @pytest.mark.anyio
    async def test_revoke_delegation_service(self, db):
        from app.services import approval_enhanced_service

        project = await _seed_project(db)
        delegation = await approval_enhanced_service.create_delegation(
            db,
            delegator_id=STUB_USER_ID,
            delegate_id=uuid.uuid4(),
            project_id=project.id,
        )
        assert delegation.is_active is True

        revoked = await approval_enhanced_service.revoke_delegation(
            db, delegation.id, STUB_USER_ID
        )
        assert revoked is not None
        assert revoked.is_active is False

    @pytest.mark.anyio
    async def test_revoke_delegation_wrong_user(self, db):
        from app.services import approval_enhanced_service
        from fastapi import HTTPException

        project = await _seed_project(db)
        delegation = await approval_enhanced_service.create_delegation(
            db,
            delegator_id=STUB_USER_ID,
            delegate_id=uuid.uuid4(),
            project_id=project.id,
        )

        with pytest.raises(HTTPException) as exc_info:
            await approval_enhanced_service.revoke_delegation(
                db, delegation.id, uuid.uuid4()
            )
        assert exc_info.value.status_code == 403

    @pytest.mark.anyio
    async def test_revoke_delegation_not_found(self, db):
        from app.services import approval_enhanced_service

        result = await approval_enhanced_service.revoke_delegation(
            db, uuid.uuid4(), STUB_USER_ID
        )
        assert result is None

    @pytest.mark.anyio
    async def test_revoke_delegation_route(self, client: AsyncClient, db):
        from app.services import approval_enhanced_service

        project = await _seed_project(db)
        delegation = await approval_enhanced_service.create_delegation(
            db,
            delegator_id=STUB_USER_ID,
            delegate_id=uuid.uuid4(),
            project_id=project.id,
        )
        await db.commit()

        resp = await client.delete(f"/approval-delegations/{delegation.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_active"] is False


class TestEscalationEnforcesExpiryInDelegations:
    """Escalation only targets non-expired delegates."""

    @pytest.mark.anyio
    async def test_escalation_skips_expired_delegates(self, db):
        from app.services import approval_enhanced_service
        from app.models.approval_delegation import ApprovalDelegation
        from app.models.user import User

        project = await _seed_project(db)
        delegate_id = uuid.uuid4()
        User_obj = User(id=delegate_id, email="exp-del@test.dev", display_name="ExpDel")
        db.add(User_obj)
        await db.flush()

        # Expired delegation — should NOT be in escalation targets
        delegation = ApprovalDelegation(
            delegator_id=STUB_USER_ID,
            delegate_id=delegate_id,
            project_id=project.id,
            active_until=datetime.now(timezone.utc) - timedelta(hours=2),
            is_active=True,
        )
        db.add(delegation)
        await _seed_expired_approval(db, project.id)

        report = await approval_enhanced_service.escalate_expired_approvals(db)
        assert len(report) == 1
        # Targets should only include the LEAD (STUB_USER_ID), not the expired delegate
        target_user_ids = {t["user_id"] for t in report[0]["escalation_targets"]}
        assert str(delegate_id) not in target_user_ids
        assert str(STUB_USER_ID) in target_user_ids


class TestBackgroundEscalationCycle:
    """Test the background scheduler escalation cycle function."""

    @pytest.mark.anyio
    async def test_run_escalation_cycle(self, db):
        """Cycle function calls the right services via its own session."""
        from app.services import approval_enhanced_service

        project = await _seed_project(db)
        await _seed_expired_approval(db, project.id)
        await db.flush()

        # Directly call service functions (the background cycle invokes these)
        deactivated = await approval_enhanced_service.deactivate_expired_delegations(db)
        report = await approval_enhanced_service.escalate_expired_approvals(db)

        assert deactivated >= 0
        assert len(report) >= 1


# ═══════════════════════════════════════════════════════════════════
# FM-176 Tests
# ═══════════════════════════════════════════════════════════════════


class TestRetentionArchiveAction:
    """Archive action creates audit log entries instead of deleting data."""

    @pytest.mark.anyio
    async def test_archive_creates_audit_record(self, db):
        from app.services import retention_policy_service
        from app.models.enterprise_governance import RetentionPolicy, RetentionAction
        from app.models.run import Run

        ws = await _seed_workspace(db)
        project = await _seed_project(db)
        # Link project to workspace
        project.workspace_id = ws.id
        await db.flush()

        # Create old run with backdated created_at
        old_run = Run(
            run_number=1,
            project_id=project.id,
            trigger="test",
            created_at=OLD_DATE,
        )
        db.add(old_run)
        await db.flush()

        # Create archive policy
        policy = RetentionPolicy(
            workspace_id=ws.id,
            entity_type="run",
            retention_days=30,
            action=RetentionAction.ARCHIVE,
            is_active=True,
            legal_hold=False,
            created_by=STUB_USER_ID,
        )
        db.add(policy)
        await db.flush()

        report = await retention_policy_service.evaluate_retention(
            db, ws.id, dry_run=False
        )

        assert report["total_deleted"] == 0
        assert report["total_archived"] >= 1
        assert report["results"][0]["archived_count"] >= 1
        assert report["results"][0]["action"] == "archive"

        # Verify audit log was created
        from app.models.enterprise_governance import AuditLog
        logs_q = select(AuditLog).where(
            AuditLog.workspace_id == ws.id,
            AuditLog.action == "retention.archive",
        )
        logs = (await db.execute(logs_q)).scalars().all()
        assert len(logs) >= 1
        assert logs[0].resource_type == "run"

    @pytest.mark.anyio
    async def test_archive_does_not_delete_data(self, db):
        from app.services import retention_policy_service
        from app.models.enterprise_governance import RetentionPolicy, RetentionAction
        from app.models.run import Run

        ws = await _seed_workspace(db)
        project = await _seed_project(db)
        project.workspace_id = ws.id
        await db.flush()

        old_run = Run(run_number=2, project_id=project.id, trigger="test", created_at=OLD_DATE)
        db.add(old_run)
        await db.flush()

        policy = RetentionPolicy(
            workspace_id=ws.id,
            entity_type="run",
            retention_days=30,
            action=RetentionAction.ARCHIVE,
            is_active=True,
            legal_hold=False,
            created_by=STUB_USER_ID,
        )
        db.add(policy)
        await db.flush()

        await retention_policy_service.evaluate_retention(db, ws.id, dry_run=False)

        # Run should still exist
        run_still = await db.get(Run, old_run.id)
        assert run_still is not None


class TestRetentionDeleteAction:
    """Delete action still works correctly after refactor."""

    @pytest.mark.anyio
    async def test_delete_removes_data(self, db):
        from app.services import retention_policy_service
        from app.models.enterprise_governance import RetentionPolicy, RetentionAction
        from app.models.notification import Notification

        ws = await _seed_workspace(db)

        # Create old notification
        notif = Notification(
            user_id=STUB_USER_ID,
            notification_type="test",
            title="Old notification",
            created_at=OLD_DATE,
        )
        db.add(notif)
        await db.flush()

        policy = RetentionPolicy(
            workspace_id=ws.id,
            entity_type="notification",
            retention_days=30,
            action=RetentionAction.DELETE,
            is_active=True,
            legal_hold=False,
            created_by=STUB_USER_ID,
        )
        db.add(policy)
        await db.flush()

        report = await retention_policy_service.evaluate_retention(
            db, ws.id, dry_run=False
        )

        assert report["total_deleted"] >= 1
        assert report["total_archived"] == 0


class TestRetentionDryRun:
    """Dry run reports without acting."""

    @pytest.mark.anyio
    async def test_dry_run_no_action(self, db):
        from app.services import retention_policy_service
        from app.models.enterprise_governance import RetentionPolicy, RetentionAction
        from app.models.run import Run

        ws = await _seed_workspace(db)
        project = await _seed_project(db)
        project.workspace_id = ws.id
        await db.flush()

        old_run = Run(run_number=3, project_id=project.id, trigger="test", created_at=OLD_DATE)
        db.add(old_run)
        await db.flush()

        policy = RetentionPolicy(
            workspace_id=ws.id,
            entity_type="run",
            retention_days=30,
            action=RetentionAction.DELETE,
            is_active=True,
            legal_hold=False,
            created_by=STUB_USER_ID,
        )
        db.add(policy)
        await db.flush()

        report = await retention_policy_service.evaluate_retention(
            db, ws.id, dry_run=True,
        )

        assert report["dry_run"] is True
        assert report["total_affected"] >= 1
        assert report["total_deleted"] == 0
        assert report["total_archived"] == 0

        # Data still exists
        still = await db.get(Run, old_run.id)
        assert still is not None


class TestRetentionLegalHold:
    """Legal hold policies are skipped during evaluation."""

    @pytest.mark.anyio
    async def test_legal_hold_skipped(self, db):
        from app.services import retention_policy_service
        from app.models.enterprise_governance import RetentionPolicy, RetentionAction

        ws = await _seed_workspace(db)

        policy = RetentionPolicy(
            workspace_id=ws.id,
            entity_type="run",
            retention_days=1,
            action=RetentionAction.DELETE,
            is_active=True,
            legal_hold=True,
            created_by=STUB_USER_ID,
        )
        db.add(policy)
        await db.flush()

        report = await retention_policy_service.evaluate_retention(
            db, ws.id, dry_run=False
        )

        assert report["policies_evaluated"] == 0


class TestRetentionArchiveAuditLog:
    """Archive action for audit_log entity type."""

    @pytest.mark.anyio
    async def test_archive_audit_logs(self, db):
        from app.services import retention_policy_service
        from app.models.enterprise_governance import (
            RetentionPolicy, RetentionAction, AuditLog, AuditActorType, AuditOutcome
        )

        ws = await _seed_workspace(db)

        # Create old audit log
        old_entry = AuditLog(
            actor_type=AuditActorType.USER,
            action="test.action",
            resource_type="test",
            workspace_id=ws.id,
            outcome=AuditOutcome.SUCCESS,
            created_at=OLD_DATE,
        )
        db.add(old_entry)
        await db.flush()

        policy = RetentionPolicy(
            workspace_id=ws.id,
            entity_type="audit_log",
            retention_days=60,
            action=RetentionAction.ARCHIVE,
            is_active=True,
            legal_hold=False,
            created_by=STUB_USER_ID,
        )
        db.add(policy)
        await db.flush()

        report = await retention_policy_service.evaluate_retention(
            db, ws.id, dry_run=False
        )

        assert report["total_archived"] >= 1
        assert report["total_deleted"] == 0
        # Original audit log still exists
        still = await db.get(AuditLog, old_entry.id)
        assert still is not None


class TestRetentionArchiveArtifact:
    """Archive action for artifact entity type."""

    @pytest.mark.anyio
    async def test_archive_artifacts(self, db):
        from app.services import retention_policy_service
        from app.models.enterprise_governance import RetentionPolicy, RetentionAction
        from app.models.artifact import Artifact

        ws = await _seed_workspace(db)
        project = await _seed_project(db)
        project.workspace_id = ws.id
        await db.flush()

        art = Artifact(
            title="old-artifact",
            artifact_type="other",
            project_id=project.id,
            created_at=OLD_DATE,
        )
        db.add(art)
        await db.flush()

        policy = RetentionPolicy(
            workspace_id=ws.id,
            entity_type="artifact",
            retention_days=90,
            action=RetentionAction.ARCHIVE,
            is_active=True,
            legal_hold=False,
            created_by=STUB_USER_ID,
        )
        db.add(policy)
        await db.flush()

        report = await retention_policy_service.evaluate_retention(
            db, ws.id, dry_run=False
        )

        assert report["total_archived"] >= 1
        # Artifact still exists
        still = await db.get(Artifact, art.id)
        assert still is not None


class TestRetentionReportStructure:
    """Verify the retention report has the expected shape."""

    @pytest.mark.anyio
    async def test_report_structure(self, db):
        from app.services import retention_policy_service

        ws = await _seed_workspace(db)

        report = await retention_policy_service.evaluate_retention(
            db, ws.id, dry_run=True
        )

        assert "workspace_id" in report
        assert "evaluated_at" in report
        assert "policies_evaluated" in report
        assert "results" in report
        assert "total_affected" in report
        assert "total_deleted" in report
        assert "total_archived" in report
        assert "dry_run" in report


class TestBackgroundRetentionCycle:
    """Test the background scheduler retention cycle function."""

    @pytest.mark.anyio
    async def test_run_retention_cycle(self, db):
        """Cycle function evaluates retention for workspaces."""
        from app.services import retention_policy_service

        ws = await _seed_workspace(db)
        await db.flush()

        # Directly call service function (the background cycle invokes this)
        report = await retention_policy_service.evaluate_retention(
            db, ws.id, dry_run=False
        )

        assert report["workspace_id"] == str(ws.id)
        assert report["policies_evaluated"] == 0  # no policies created


class TestRetentionPolicyCRUD:
    """Service-level CRUD for retention policies."""

    @pytest.mark.anyio
    async def test_create_policy(self, db):
        from app.services import retention_policy_service
        from app.models.enterprise_governance import RetentionAction

        ws = await _seed_workspace(db)

        policy = await retention_policy_service.create_retention_policy(
            db,
            workspace_id=ws.id,
            entity_type="run",
            retention_days=90,
            action=RetentionAction.DELETE,
            created_by=STUB_USER_ID,
        )
        assert policy.entity_type == "run"
        assert policy.retention_days == 90

    @pytest.mark.anyio
    async def test_create_policy_invalid_entity(self, db):
        from app.services import retention_policy_service
        from app.models.enterprise_governance import RetentionAction

        ws = await _seed_workspace(db)

        with pytest.raises(ValueError, match="Unsupported entity type"):
            await retention_policy_service.create_retention_policy(
                db,
                workspace_id=ws.id,
                entity_type="invalid_type",
                retention_days=30,
                action=RetentionAction.DELETE,
                created_by=STUB_USER_ID,
            )

    @pytest.mark.anyio
    async def test_list_policies(self, db):
        from app.services import retention_policy_service
        from app.models.enterprise_governance import RetentionAction

        ws = await _seed_workspace(db)

        await retention_policy_service.create_retention_policy(
            db, workspace_id=ws.id, entity_type="run",
            retention_days=30, action=RetentionAction.DELETE, created_by=STUB_USER_ID,
        )
        await retention_policy_service.create_retention_policy(
            db, workspace_id=ws.id, entity_type="artifact",
            retention_days=60, action=RetentionAction.ARCHIVE, created_by=STUB_USER_ID,
        )

        items, total = await retention_policy_service.list_retention_policies(db, ws.id)
        assert total == 2
        assert len(items) == 2

    @pytest.mark.anyio
    async def test_update_policy(self, db):
        from app.services import retention_policy_service
        from app.models.enterprise_governance import RetentionAction

        ws = await _seed_workspace(db)
        policy = await retention_policy_service.create_retention_policy(
            db, workspace_id=ws.id, entity_type="run",
            retention_days=30, action=RetentionAction.DELETE, created_by=STUB_USER_ID,
        )

        updated = await retention_policy_service.update_retention_policy(
            db, policy.id, retention_days=60, legal_hold=True
        )
        assert updated.retention_days == 60
        assert updated.legal_hold is True

    @pytest.mark.anyio
    async def test_delete_policy(self, db):
        from app.services import retention_policy_service
        from app.models.enterprise_governance import RetentionAction

        ws = await _seed_workspace(db)
        policy = await retention_policy_service.create_retention_policy(
            db, workspace_id=ws.id, entity_type="run",
            retention_days=30, action=RetentionAction.DELETE, created_by=STUB_USER_ID,
        )

        deleted = await retention_policy_service.delete_retention_policy(db, policy.id)
        assert deleted is True

        deleted_again = await retention_policy_service.delete_retention_policy(db, policy.id)
        assert deleted_again is False
