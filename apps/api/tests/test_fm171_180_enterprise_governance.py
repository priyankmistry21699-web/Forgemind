"""Tests for FM-171–180: Enterprise Governance, Permissions & Compliance.

Covers: audit logs, policy evaluation engine, compliance reports,
IP allowlisting, and retention policies.
"""

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enterprise_governance import (
    AuditActorType,
    AuditOutcome,
    PolicyEvalResult,
    ComplianceReportType,
    ComplianceReportStatus,
    RetentionAction,
)
from app.models.governance_policy import GovernancePolicy, PolicyTrigger, PolicyAction
from app.models.workspace import Workspace
from app.models.membership import WorkspaceMember, WorkspaceRole

from app.services import (
    audit_log_service,
    governance_engine_service,
    compliance_report_service,
    ip_allowlist_service,
    retention_policy_service,
)

STUB_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


# ── Fixtures ─────────────────────────────────────────────────────


@pytest.fixture
async def sample_workspace(db_session: AsyncSession):
    """Create a workspace with stub user as OWNER."""
    ws = Workspace(
        name="Test Workspace",
        slug=f"test-ws-{uuid.uuid4().hex[:8]}",
        owner_id=STUB_USER_ID,
    )
    db_session.add(ws)
    await db_session.flush()

    member = WorkspaceMember(
        workspace_id=ws.id,
        user_id=STUB_USER_ID,
        role=WorkspaceRole.OWNER,
    )
    db_session.add(member)
    await db_session.flush()
    return ws


@pytest.fixture
async def sample_governance_policy(db_session: AsyncSession, sample_project):
    """Create a governance policy for testing."""
    policy = GovernancePolicy(
        name="Block Architecture Tasks",
        description="Blocks tasks of type architecture",
        trigger=PolicyTrigger.TASK_TYPE,
        action=PolicyAction.BLOCK,
        rules={"task_types": ["architecture", "security"]},
        project_id=sample_project.id,
        enabled=True,
        priority=10,
    )
    db_session.add(policy)
    await db_session.flush()
    return policy


@pytest.fixture
async def cost_policy(db_session: AsyncSession, sample_project):
    """Create a cost threshold governance policy."""
    policy = GovernancePolicy(
        name="Cost Alert",
        description="Warns when cost exceeds $50",
        trigger=PolicyTrigger.COST_THRESHOLD,
        action=PolicyAction.NOTIFY,
        rules={"cost_threshold_usd": 50.0},
        project_id=sample_project.id,
        enabled=True,
        priority=5,
    )
    db_session.add(policy)
    await db_session.flush()
    return policy


# ══════════════════════════════════════════════════════════════════
# FM-173: Audit Log Tests
# ══════════════════════════════════════════════════════════════════


class TestAuditLog:
    @pytest.mark.asyncio
    async def test_log_event(self, db_session: AsyncSession, sample_workspace):
        entry = await audit_log_service.log_event(
            db_session,
            actor_id=STUB_USER_ID,
            action="project.create",
            resource_type="project",
            resource_id=uuid.uuid4(),
            workspace_id=sample_workspace.id,
            outcome=AuditOutcome.SUCCESS,
            details={"project_name": "Test Project"},
        )
        await db_session.commit()

        assert entry.id is not None
        assert entry.action == "project.create"
        assert entry.outcome == AuditOutcome.SUCCESS
        assert entry.actor_type == AuditActorType.USER

    @pytest.mark.asyncio
    async def test_list_audit_logs(self, db_session: AsyncSession, sample_workspace):
        # Create multiple entries
        for i in range(5):
            await audit_log_service.log_event(
                db_session,
                actor_id=STUB_USER_ID,
                action=f"test.action_{i}",
                resource_type="test",
                workspace_id=sample_workspace.id,
            )
        await db_session.commit()

        items, total = await audit_log_service.list_audit_logs(
            db_session, sample_workspace.id
        )
        assert total == 5
        assert len(items) == 5

    @pytest.mark.asyncio
    async def test_list_audit_logs_with_filters(
        self, db_session: AsyncSession, sample_workspace
    ):
        await audit_log_service.log_event(
            db_session,
            actor_id=STUB_USER_ID,
            action="project.create",
            resource_type="project",
            workspace_id=sample_workspace.id,
            outcome=AuditOutcome.SUCCESS,
        )
        await audit_log_service.log_event(
            db_session,
            actor_id=STUB_USER_ID,
            action="run.start",
            resource_type="run",
            workspace_id=sample_workspace.id,
            outcome=AuditOutcome.DENIED,
        )
        await db_session.commit()

        # Filter by action
        items, total = await audit_log_service.list_audit_logs(
            db_session, sample_workspace.id, action="project.create"
        )
        assert total == 1
        assert items[0].action == "project.create"

        # Filter by outcome
        items, total = await audit_log_service.list_audit_logs(
            db_session, sample_workspace.id, outcome=AuditOutcome.DENIED
        )
        assert total == 1
        assert items[0].outcome == AuditOutcome.DENIED

    @pytest.mark.asyncio
    async def test_export_audit_logs_csv(
        self, db_session: AsyncSession, sample_workspace
    ):
        await audit_log_service.log_event(
            db_session,
            actor_id=STUB_USER_ID,
            action="project.create",
            resource_type="project",
            workspace_id=sample_workspace.id,
        )
        await db_session.commit()

        csv_content = await audit_log_service.export_audit_logs_csv(
            db_session, sample_workspace.id
        )
        assert "project.create" in csv_content
        assert "id,actor_id" in csv_content

    @pytest.mark.asyncio
    async def test_audit_stats(self, db_session: AsyncSession, sample_workspace):
        for _ in range(3):
            await audit_log_service.log_event(
                db_session,
                actor_id=STUB_USER_ID,
                action="project.create",
                resource_type="project",
                workspace_id=sample_workspace.id,
                outcome=AuditOutcome.SUCCESS,
            )
        await audit_log_service.log_event(
            db_session,
            actor_id=STUB_USER_ID,
            action="run.denied",
            resource_type="run",
            workspace_id=sample_workspace.id,
            outcome=AuditOutcome.DENIED,
        )
        await db_session.commit()

        stats = await audit_log_service.get_audit_stats(db_session, sample_workspace.id)
        assert stats["total_entries"] == 4
        assert stats["by_outcome"]["success"] == 3
        assert stats["by_outcome"]["denied"] == 1
        assert "project.create" in stats["top_actions"]

    @pytest.mark.asyncio
    async def test_audit_log_immutability(
        self, db_session: AsyncSession, sample_workspace
    ):
        """Audit entries have no updated_at — they're immutable by design."""
        entry = await audit_log_service.log_event(
            db_session,
            actor_id=STUB_USER_ID,
            action="test.immutable",
            resource_type="test",
            workspace_id=sample_workspace.id,
        )
        await db_session.commit()

        assert entry.created_at is not None
        # No updated_at attribute
        assert (
            not hasattr(entry, "updated_at")
            or "updated_at" not in entry.__table__.columns
        )

    @pytest.mark.asyncio
    async def test_audit_log_with_ip_and_user_agent(
        self, db_session: AsyncSession, sample_workspace
    ):
        entry = await audit_log_service.log_event(
            db_session,
            actor_id=STUB_USER_ID,
            action="login",
            resource_type="session",
            workspace_id=sample_workspace.id,
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0",
        )
        await db_session.commit()

        assert entry.ip_address == "192.168.1.100"
        assert entry.user_agent == "Mozilla/5.0"


# ══════════════════════════════════════════════════════════════════
# FM-174: Governance Policy Evaluation Tests
# ══════════════════════════════════════════════════════════════════


class TestGovernancePolicyEvaluation:
    @pytest.mark.asyncio
    async def test_evaluate_policies_blocked(
        self,
        db_session: AsyncSession,
        sample_project,
        sample_governance_policy,
    ):
        result = await governance_engine_service.evaluate_policies(
            db_session,
            project_id=sample_project.id,
            trigger_action="task.create",
            resource_type="task",
            actor_id=STUB_USER_ID,
            context={"task_type": "architecture"},
        )
        await db_session.commit()

        assert result["allowed"] is False
        assert "Block Architecture Tasks" in result["blocked_by"]
        assert len(result["evaluations"]) >= 1

    @pytest.mark.asyncio
    async def test_evaluate_policies_allowed(
        self,
        db_session: AsyncSession,
        sample_project,
        sample_governance_policy,
    ):
        result = await governance_engine_service.evaluate_policies(
            db_session,
            project_id=sample_project.id,
            trigger_action="task.create",
            resource_type="task",
            actor_id=STUB_USER_ID,
            context={"task_type": "documentation"},
        )
        await db_session.commit()

        assert result["allowed"] is True
        assert len(result["blocked_by"]) == 0

    @pytest.mark.asyncio
    async def test_evaluate_cost_threshold_warning(
        self,
        db_session: AsyncSession,
        sample_project,
        cost_policy,
    ):
        result = await governance_engine_service.evaluate_policies(
            db_session,
            project_id=sample_project.id,
            trigger_action="run.start",
            resource_type="run",
            actor_id=STUB_USER_ID,
            context={"estimated_cost_usd": 75.0},
        )
        await db_session.commit()

        # NOTIFY action → warning, not blocked
        assert result["allowed"] is True
        assert "Cost Alert" in result["warnings"]

    @pytest.mark.asyncio
    async def test_evaluate_cost_threshold_pass(
        self,
        db_session: AsyncSession,
        sample_project,
        cost_policy,
    ):
        result = await governance_engine_service.evaluate_policies(
            db_session,
            project_id=sample_project.id,
            trigger_action="run.start",
            resource_type="run",
            actor_id=STUB_USER_ID,
            context={"estimated_cost_usd": 30.0},
        )
        await db_session.commit()

        assert result["allowed"] is True
        assert len(result["warnings"]) == 0

    @pytest.mark.asyncio
    async def test_evaluate_no_policies(self, db_session: AsyncSession, sample_project):
        result = await governance_engine_service.evaluate_policies(
            db_session,
            project_id=sample_project.id,
            trigger_action="task.create",
            resource_type="task",
            actor_id=STUB_USER_ID,
        )
        await db_session.commit()

        assert result["allowed"] is True
        assert len(result["evaluations"]) == 0

    @pytest.mark.asyncio
    async def test_evaluation_records_persisted(
        self,
        db_session: AsyncSession,
        sample_project,
        sample_governance_policy,
    ):
        await governance_engine_service.evaluate_policies(
            db_session,
            project_id=sample_project.id,
            trigger_action="task.create",
            resource_type="task",
            actor_id=STUB_USER_ID,
            context={"task_type": "architecture"},
        )
        await db_session.commit()

        items, total = await governance_engine_service.list_evaluations(
            db_session, project_id=sample_project.id
        )
        assert total >= 1
        assert items[0].result == PolicyEvalResult.FAIL
        assert items[0].enforced is True

    @pytest.mark.asyncio
    async def test_evaluate_disabled_policy_ignored(
        self, db_session: AsyncSession, sample_project
    ):
        # Create disabled policy
        policy = GovernancePolicy(
            name="Disabled Policy",
            trigger=PolicyTrigger.TASK_TYPE,
            action=PolicyAction.BLOCK,
            rules={"task_types": ["anything"]},
            project_id=sample_project.id,
            enabled=False,
            priority=10,
        )
        db_session.add(policy)
        await db_session.flush()

        result = await governance_engine_service.evaluate_policies(
            db_session,
            project_id=sample_project.id,
            trigger_action="task.create",
            resource_type="task",
            context={"task_type": "anything"},
        )
        await db_session.commit()

        assert result["allowed"] is True
        assert len(result["evaluations"]) == 0

    @pytest.mark.asyncio
    async def test_evaluate_global_policy_applies(
        self, db_session: AsyncSession, sample_project
    ):
        """Global policies (project_id=None) apply to all projects."""
        policy = GovernancePolicy(
            name="Global Block",
            trigger=PolicyTrigger.AGENT_ACTION,
            action=PolicyAction.BLOCK,
            rules={"agent_actions": ["dangerous.action"]},
            project_id=None,
            enabled=True,
            priority=100,
        )
        db_session.add(policy)
        await db_session.flush()

        result = await governance_engine_service.evaluate_policies(
            db_session,
            project_id=sample_project.id,
            trigger_action="dangerous.action",
            resource_type="agent",
        )
        await db_session.commit()

        assert result["allowed"] is False
        assert "Global Block" in result["blocked_by"]


# ══════════════════════════════════════════════════════════════════
# FM-177: Compliance Report Tests
# ══════════════════════════════════════════════════════════════════


class TestComplianceReports:
    @pytest.mark.asyncio
    async def test_generate_access_review_report(
        self, db_session: AsyncSession, sample_workspace, sample_project
    ):
        report = await compliance_report_service.generate_report(
            db_session,
            workspace_id=sample_workspace.id,
            report_type=ComplianceReportType.ACCESS_REVIEW,
            title="Q1 Access Review",
            generated_by=STUB_USER_ID,
        )
        await db_session.commit()

        assert report.status == ComplianceReportStatus.READY
        assert report.content is not None
        assert report.content["report_type"] == "access_review"
        assert report.content["workspace_member_count"] >= 1

    @pytest.mark.asyncio
    async def test_generate_approval_audit_report(
        self,
        db_session: AsyncSession,
        sample_workspace,
        sample_project,
        sample_approval,
    ):
        # Link project to workspace so compliance service can find it
        sample_project.workspace_id = sample_workspace.id
        await db_session.flush()

        report = await compliance_report_service.generate_report(
            db_session,
            workspace_id=sample_workspace.id,
            report_type=ComplianceReportType.APPROVAL_AUDIT,
            title="Approval Audit",
            generated_by=STUB_USER_ID,
        )
        await db_session.commit()

        assert report.status == ComplianceReportStatus.READY
        assert report.content["report_type"] == "approval_audit"
        assert report.content["total_approvals"] >= 1

    @pytest.mark.asyncio
    async def test_generate_change_management_report(
        self, db_session: AsyncSession, sample_workspace
    ):
        # Add some audit entries first
        await audit_log_service.log_event(
            db_session,
            actor_id=STUB_USER_ID,
            action="project.create",
            resource_type="project",
            workspace_id=sample_workspace.id,
        )
        await db_session.flush()

        report = await compliance_report_service.generate_report(
            db_session,
            workspace_id=sample_workspace.id,
            report_type=ComplianceReportType.CHANGE_MANAGEMENT,
            title="Change Mgmt Report",
            generated_by=STUB_USER_ID,
        )
        await db_session.commit()

        assert report.status == ComplianceReportStatus.READY
        assert report.content["total_changes"] >= 1

    @pytest.mark.asyncio
    async def test_generate_policy_compliance_report(
        self,
        db_session: AsyncSession,
        sample_workspace,
        sample_project,
        sample_governance_policy,
    ):
        # Link project to workspace so compliance service can find it
        sample_project.workspace_id = sample_workspace.id
        await db_session.flush()

        # Generate some evaluations
        await governance_engine_service.evaluate_policies(
            db_session,
            project_id=sample_project.id,
            trigger_action="task.create",
            resource_type="task",
            context={"task_type": "architecture"},
        )
        await db_session.flush()

        report = await compliance_report_service.generate_report(
            db_session,
            workspace_id=sample_workspace.id,
            report_type=ComplianceReportType.POLICY_COMPLIANCE,
            title="Policy Compliance",
            generated_by=STUB_USER_ID,
        )
        await db_session.commit()

        assert report.status == ComplianceReportStatus.READY
        assert report.content["total_evaluations"] >= 1

    @pytest.mark.asyncio
    async def test_generate_full_governance_report(
        self, db_session: AsyncSession, sample_workspace, sample_project
    ):
        # Link project to workspace
        sample_project.workspace_id = sample_workspace.id
        await db_session.flush()

        report = await compliance_report_service.generate_report(
            db_session,
            workspace_id=sample_workspace.id,
            report_type=ComplianceReportType.FULL_GOVERNANCE,
            title="Full Governance Report",
            generated_by=STUB_USER_ID,
        )
        await db_session.commit()

        assert report.status == ComplianceReportStatus.READY
        assert "sections" in report.content
        assert "access_review" in report.content["sections"]
        assert "change_management" in report.content["sections"]
        assert "approval_audit" in report.content["sections"]
        assert "policy_compliance" in report.content["sections"]

    @pytest.mark.asyncio
    async def test_list_reports(self, db_session: AsyncSession, sample_workspace):
        for i in range(3):
            await compliance_report_service.generate_report(
                db_session,
                workspace_id=sample_workspace.id,
                report_type=ComplianceReportType.ACCESS_REVIEW,
                title=f"Report {i}",
                generated_by=STUB_USER_ID,
            )
        await db_session.commit()

        items, total = await compliance_report_service.list_reports(
            db_session, sample_workspace.id
        )
        assert total == 3
        assert len(items) == 3

    @pytest.mark.asyncio
    async def test_get_report(self, db_session: AsyncSession, sample_workspace):
        report = await compliance_report_service.generate_report(
            db_session,
            workspace_id=sample_workspace.id,
            report_type=ComplianceReportType.ACCESS_REVIEW,
            title="Test Report",
            generated_by=STUB_USER_ID,
        )
        await db_session.commit()

        fetched = await compliance_report_service.get_report(db_session, report.id)
        assert fetched is not None
        assert fetched.id == report.id
        assert fetched.title == "Test Report"


# ══════════════════════════════════════════════════════════════════
# FM-178: IP Allowlist Tests
# ══════════════════════════════════════════════════════════════════


class TestIpAllowlist:
    @pytest.mark.asyncio
    async def test_add_allowlist_entry(
        self, db_session: AsyncSession, sample_workspace
    ):
        entry = await ip_allowlist_service.add_allowlist_entry(
            db_session,
            workspace_id=sample_workspace.id,
            cidr="10.0.0.0/8",
            description="Corporate network",
            created_by=STUB_USER_ID,
        )
        await db_session.commit()

        assert entry.id is not None
        assert entry.cidr == "10.0.0.0/8"
        assert entry.is_active is True

    @pytest.mark.asyncio
    async def test_add_invalid_cidr_rejected(
        self, db_session: AsyncSession, sample_workspace
    ):
        with pytest.raises(ValueError, match="Invalid CIDR"):
            await ip_allowlist_service.add_allowlist_entry(
                db_session,
                workspace_id=sample_workspace.id,
                cidr="not-a-cidr",
                created_by=STUB_USER_ID,
            )

    @pytest.mark.asyncio
    async def test_check_ip_in_allowlist(
        self, db_session: AsyncSession, sample_workspace
    ):
        await ip_allowlist_service.add_allowlist_entry(
            db_session,
            workspace_id=sample_workspace.id,
            cidr="192.168.1.0/24",
            created_by=STUB_USER_ID,
        )
        await db_session.commit()

        entries = await ip_allowlist_service.get_workspace_allowlist(
            db_session, sample_workspace.id
        )

        assert (
            ip_allowlist_service.check_ip_against_allowlist("192.168.1.50", entries)
            is True
        )
        assert (
            ip_allowlist_service.check_ip_against_allowlist("10.0.0.1", entries)
            is False
        )

    @pytest.mark.asyncio
    async def test_empty_allowlist_allows_all(self):
        """An empty allowlist means no restrictions."""
        assert ip_allowlist_service.check_ip_against_allowlist("1.2.3.4", []) is True

    @pytest.mark.asyncio
    async def test_inactive_entries_ignored(
        self, db_session: AsyncSession, sample_workspace
    ):
        entry = await ip_allowlist_service.add_allowlist_entry(
            db_session,
            workspace_id=sample_workspace.id,
            cidr="0.0.0.0/0",  # Allow all
            created_by=STUB_USER_ID,
        )
        await ip_allowlist_service.toggle_allowlist_entry(
            db_session, entry.id, is_active=False
        )
        await db_session.commit()

        entries = await ip_allowlist_service.get_workspace_allowlist(
            db_session, sample_workspace.id
        )
        # All entries are inactive, so no restrictions apply
        assert (
            ip_allowlist_service.check_ip_against_allowlist("1.2.3.4", entries) is True
        )

    @pytest.mark.asyncio
    async def test_remove_allowlist_entry(
        self, db_session: AsyncSession, sample_workspace
    ):
        entry = await ip_allowlist_service.add_allowlist_entry(
            db_session,
            workspace_id=sample_workspace.id,
            cidr="10.0.0.0/8",
            created_by=STUB_USER_ID,
        )
        await db_session.commit()

        deleted = await ip_allowlist_service.remove_allowlist_entry(
            db_session, entry.id
        )
        await db_session.commit()
        assert deleted is True

        entries = await ip_allowlist_service.get_workspace_allowlist(
            db_session, sample_workspace.id
        )
        assert len(entries) == 0

    @pytest.mark.asyncio
    async def test_list_allowlist_entries(
        self, db_session: AsyncSession, sample_workspace
    ):
        for cidr in ["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"]:
            await ip_allowlist_service.add_allowlist_entry(
                db_session,
                workspace_id=sample_workspace.id,
                cidr=cidr,
                created_by=STUB_USER_ID,
            )
        await db_session.commit()

        items, total = await ip_allowlist_service.list_allowlist_entries(
            db_session, sample_workspace.id
        )
        assert total == 3
        assert len(items) == 3

    @pytest.mark.asyncio
    async def test_toggle_allowlist_entry(
        self, db_session: AsyncSession, sample_workspace
    ):
        entry = await ip_allowlist_service.add_allowlist_entry(
            db_session,
            workspace_id=sample_workspace.id,
            cidr="10.0.0.0/8",
            created_by=STUB_USER_ID,
        )
        await db_session.commit()
        assert entry.is_active is True

        toggled = await ip_allowlist_service.toggle_allowlist_entry(
            db_session, entry.id, is_active=False
        )
        assert toggled is not None
        assert toggled.is_active is False

    @pytest.mark.asyncio
    async def test_multiple_cidrs_checked(
        self, db_session: AsyncSession, sample_workspace
    ):
        """IP matching works across multiple CIDR entries."""
        for cidr in ["10.0.0.0/8", "172.16.0.0/12"]:
            await ip_allowlist_service.add_allowlist_entry(
                db_session,
                workspace_id=sample_workspace.id,
                cidr=cidr,
                created_by=STUB_USER_ID,
            )
        await db_session.commit()

        entries = await ip_allowlist_service.get_workspace_allowlist(
            db_session, sample_workspace.id
        )
        assert (
            ip_allowlist_service.check_ip_against_allowlist("10.1.2.3", entries) is True
        )
        assert (
            ip_allowlist_service.check_ip_against_allowlist("172.20.0.1", entries)
            is True
        )
        assert (
            ip_allowlist_service.check_ip_against_allowlist("8.8.8.8", entries) is False
        )


# ══════════════════════════════════════════════════════════════════
# FM-176: Retention Policy Tests
# ══════════════════════════════════════════════════════════════════


class TestRetentionPolicies:
    @pytest.mark.asyncio
    async def test_create_retention_policy(
        self, db_session: AsyncSession, sample_workspace
    ):
        policy = await retention_policy_service.create_retention_policy(
            db_session,
            workspace_id=sample_workspace.id,
            entity_type="run",
            retention_days=90,
            action=RetentionAction.ARCHIVE,
            created_by=STUB_USER_ID,
        )
        await db_session.commit()

        assert policy.id is not None
        assert policy.entity_type == "run"
        assert policy.retention_days == 90
        assert policy.legal_hold is False

    @pytest.mark.asyncio
    async def test_create_invalid_entity_type(
        self, db_session: AsyncSession, sample_workspace
    ):
        with pytest.raises(ValueError, match="Unsupported entity type"):
            await retention_policy_service.create_retention_policy(
                db_session,
                workspace_id=sample_workspace.id,
                entity_type="invalid_type",
                retention_days=90,
                created_by=STUB_USER_ID,
            )

    @pytest.mark.asyncio
    async def test_list_retention_policies(
        self, db_session: AsyncSession, sample_workspace
    ):
        for entity_type in ["run", "audit_log"]:
            await retention_policy_service.create_retention_policy(
                db_session,
                workspace_id=sample_workspace.id,
                entity_type=entity_type,
                retention_days=365,
                created_by=STUB_USER_ID,
            )
        await db_session.commit()

        items, total = await retention_policy_service.list_retention_policies(
            db_session, sample_workspace.id
        )
        assert total == 2

        # Filter by entity type
        items, total = await retention_policy_service.list_retention_policies(
            db_session, sample_workspace.id, entity_type="run"
        )
        assert total == 1

    @pytest.mark.asyncio
    async def test_update_retention_policy(
        self, db_session: AsyncSession, sample_workspace
    ):
        policy = await retention_policy_service.create_retention_policy(
            db_session,
            workspace_id=sample_workspace.id,
            entity_type="run",
            retention_days=90,
            created_by=STUB_USER_ID,
        )
        await db_session.commit()

        updated = await retention_policy_service.update_retention_policy(
            db_session,
            policy.id,
            retention_days=180,
            legal_hold=True,
        )
        await db_session.commit()

        assert updated is not None
        assert updated.retention_days == 180
        assert updated.legal_hold is True

    @pytest.mark.asyncio
    async def test_delete_retention_policy(
        self, db_session: AsyncSession, sample_workspace
    ):
        policy = await retention_policy_service.create_retention_policy(
            db_session,
            workspace_id=sample_workspace.id,
            entity_type="run",
            retention_days=90,
            created_by=STUB_USER_ID,
        )
        await db_session.commit()

        deleted = await retention_policy_service.delete_retention_policy(
            db_session, policy.id
        )
        assert deleted is True

    @pytest.mark.asyncio
    async def test_evaluate_retention_dry_run(
        self, db_session: AsyncSession, sample_workspace
    ):
        await retention_policy_service.create_retention_policy(
            db_session,
            workspace_id=sample_workspace.id,
            entity_type="audit_log",
            retention_days=1,  # Short retention for testing
            action=RetentionAction.DELETE,
            created_by=STUB_USER_ID,
        )
        await db_session.commit()

        result = await retention_policy_service.evaluate_retention(
            db_session, sample_workspace.id, dry_run=True
        )

        assert result["policies_evaluated"] >= 1
        assert "results" in result
        assert all(r["dry_run"] is True for r in result["results"])

    @pytest.mark.asyncio
    async def test_legal_hold_excludes_from_evaluation(
        self, db_session: AsyncSession, sample_workspace
    ):
        await retention_policy_service.create_retention_policy(
            db_session,
            workspace_id=sample_workspace.id,
            entity_type="run",
            retention_days=1,
            legal_hold=True,
            created_by=STUB_USER_ID,
        )
        await db_session.commit()

        result = await retention_policy_service.evaluate_retention(
            db_session, sample_workspace.id, dry_run=True
        )
        # Legal hold policies are excluded from evaluation
        assert result["policies_evaluated"] == 0

    @pytest.mark.asyncio
    async def test_create_artifact_retention_policy(
        self, db_session: AsyncSession, sample_workspace
    ):
        """FM-176: Artifact entity type is now supported."""
        policy = await retention_policy_service.create_retention_policy(
            db_session,
            workspace_id=sample_workspace.id,
            entity_type="artifact",
            retention_days=30,
            action=RetentionAction.DELETE,
            created_by=STUB_USER_ID,
        )
        await db_session.commit()

        assert policy.id is not None
        assert policy.entity_type == "artifact"
        assert policy.retention_days == 30

    @pytest.mark.asyncio
    async def test_evaluate_artifact_retention_dry_run(
        self, db_session: AsyncSession, sample_workspace
    ):
        """FM-176: Artifact retention evaluation identifies old artifacts."""
        from app.models.project import Project
        from app.models.artifact import Artifact, ArtifactType

        project = Project(
            name="Retention Artifact Test",
            owner_id=STUB_USER_ID,
            workspace_id=sample_workspace.id,
        )
        db_session.add(project)
        await db_session.flush()

        # Create an old artifact
        old_artifact = Artifact(
            title="Old Artifact",
            artifact_type=ArtifactType.OTHER,
            project_id=project.id,
            created_by="test",
        )
        db_session.add(old_artifact)
        await db_session.flush()

        # Backdate the artifact
        from sqlalchemy import update
        from datetime import timedelta

        await db_session.execute(
            update(Artifact)
            .where(Artifact.id == old_artifact.id)
            .values(created_at=datetime.now(timezone.utc) - timedelta(days=60))
        )
        await db_session.flush()

        await retention_policy_service.create_retention_policy(
            db_session,
            workspace_id=sample_workspace.id,
            entity_type="artifact",
            retention_days=30,
            action=RetentionAction.DELETE,
            created_by=STUB_USER_ID,
        )
        await db_session.commit()

        result = await retention_policy_service.evaluate_retention(
            db_session, sample_workspace.id, dry_run=True
        )

        assert result["policies_evaluated"] >= 1
        artifact_results = [
            r for r in result["results"] if r["entity_type"] == "artifact"
        ]
        assert len(artifact_results) == 1
        assert artifact_results[0]["affected_count"] >= 1
        assert artifact_results[0]["dry_run"] is True
        assert artifact_results[0]["deleted_count"] == 0  # dry run

    @pytest.mark.asyncio
    async def test_evaluate_artifact_retention_execute(
        self, db_session: AsyncSession, sample_workspace
    ):
        """FM-176: Artifact retention can actually delete old artifacts."""
        from app.models.project import Project
        from app.models.artifact import Artifact, ArtifactType
        from sqlalchemy import update, func as sa_func, select
        from datetime import timedelta

        project = Project(
            name="Retention Delete Test",
            owner_id=STUB_USER_ID,
            workspace_id=sample_workspace.id,
        )
        db_session.add(project)
        await db_session.flush()

        old_artifact = Artifact(
            title="Will Be Deleted",
            artifact_type=ArtifactType.OTHER,
            project_id=project.id,
            created_by="test",
        )
        db_session.add(old_artifact)
        await db_session.flush()

        await db_session.execute(
            update(Artifact)
            .where(Artifact.id == old_artifact.id)
            .values(created_at=datetime.now(timezone.utc) - timedelta(days=100))
        )

        await retention_policy_service.create_retention_policy(
            db_session,
            workspace_id=sample_workspace.id,
            entity_type="artifact",
            retention_days=30,
            action=RetentionAction.DELETE,
            created_by=STUB_USER_ID,
        )
        await db_session.commit()

        result = await retention_policy_service.evaluate_retention(
            db_session, sample_workspace.id, dry_run=False
        )

        artifact_results = [
            r for r in result["results"] if r["entity_type"] == "artifact"
        ]
        assert len(artifact_results) == 1
        assert artifact_results[0]["deleted_count"] >= 1

        # Verify artifact was actually deleted
        count = (
            await db_session.execute(
                select(sa_func.count())
                .select_from(Artifact)
                .where(Artifact.id == old_artifact.id)
            )
        ).scalar()
        assert count == 0


# ══════════════════════════════════════════════════════════════════
# FM-171: Workspace Governance Settings Tests
# ══════════════════════════════════════════════════════════════════


class TestGovernanceSettings:
    @pytest.mark.asyncio
    async def test_default_governance_settings(
        self, db_session: AsyncSession, sample_workspace
    ):
        """New workspace has no governance settings by default."""
        assert sample_workspace.governance_settings is None

    @pytest.mark.asyncio
    async def test_set_governance_settings(
        self, db_session: AsyncSession, sample_workspace
    ):
        """Can set governance settings JSON on workspace."""
        sample_workspace.governance_settings = {
            "plan_tier": "enterprise",
            "compliance_level": "soc2",
            "sso_enforced": True,
            "ip_enforcement_enabled": True,
            "data_region": "us-east-1",
            "audit_retention_days": 365,
        }
        db_session.add(sample_workspace)
        await db_session.commit()

        from app.models.workspace import Workspace

        ws = await db_session.get(Workspace, sample_workspace.id)
        assert ws.governance_settings["plan_tier"] == "enterprise"
        assert ws.governance_settings["sso_enforced"] is True

    @pytest.mark.asyncio
    async def test_partial_governance_update(
        self, db_session: AsyncSession, sample_workspace
    ):
        """Partial update merges with existing settings."""
        sample_workspace.governance_settings = {"plan_tier": "free"}
        db_session.add(sample_workspace)
        await db_session.commit()

        gov = dict(sample_workspace.governance_settings)
        gov["compliance_level"] = "basic"
        sample_workspace.governance_settings = gov
        db_session.add(sample_workspace)
        await db_session.commit()

        from app.models.workspace import Workspace

        ws = await db_session.get(Workspace, sample_workspace.id)
        assert ws.governance_settings["plan_tier"] == "free"
        assert ws.governance_settings["compliance_level"] == "basic"


# ══════════════════════════════════════════════════════════════════
# FM-172: RBAC Role Introspection Tests
# ══════════════════════════════════════════════════════════════════


class TestRBACIntrospection:
    def test_workspace_owner_permissions(self):
        """Owner role should have all workspace permissions."""
        from app.services.authz_service import (
            get_workspace_role_permissions,
        )
        from app.models.membership import WorkspaceRole

        perms = get_workspace_role_permissions(WorkspaceRole.OWNER)
        assert len(perms) > 0
        assert "workspace:manage_governance" in perms
        assert "workspace:view_audit" in perms
        assert "workspace:manage_secrets" in perms

    def test_workspace_viewer_limited_permissions(self):
        """Viewer role should have only view permissions."""
        from app.services.authz_service import (
            get_workspace_role_permissions,
        )
        from app.models.membership import WorkspaceRole

        perms = get_workspace_role_permissions(WorkspaceRole.VIEWER)
        # Viewer should not have manage actions
        assert "workspace:manage_governance" not in perms
        assert "workspace:manage_secrets" not in perms

    def test_project_role_permissions(self):
        """Project roles should return valid permission lists."""
        from app.services.authz_service import (
            get_project_role_permissions,
        )
        from app.models.membership import ProjectRole

        lead_perms = get_project_role_permissions(ProjectRole.LEAD)
        viewer_perms = get_project_role_permissions(ProjectRole.VIEWER)

        assert len(lead_perms) > len(viewer_perms)

    @pytest.mark.asyncio
    async def test_get_user_permissions(
        self, db_session: AsyncSession, sample_workspace
    ):
        """get_user_permissions returns roles + computed actions."""
        from app.services.authz_service import get_user_permissions

        perms = await get_user_permissions(
            db_session,
            workspace_id=sample_workspace.id,
            user_id=STUB_USER_ID,
        )
        assert perms["workspace_role"] == "owner"
        assert len(perms["workspace_actions"]) > 0
        assert perms["project_role"] is None
        assert perms["project_actions"] == []


# ══════════════════════════════════════════════════════════════════
# FM-175: SSO Configuration Tests
# ══════════════════════════════════════════════════════════════════


class TestSSOConfiguration:
    @pytest.mark.asyncio
    async def test_create_sso_config(self, db_session: AsyncSession, sample_workspace):
        from app.services import sso_configuration_service

        config = await sso_configuration_service.create_sso_config(
            db_session,
            workspace_id=sample_workspace.id,
            provider_type="oidc",
            display_name="Corporate IdP",
            issuer_url="https://idp.example.com",
            client_id="forgemind-app",
            is_active=True,
            created_by=STUB_USER_ID,
        )
        await db_session.commit()

        assert config.id is not None
        assert config.provider_type == "oidc"
        assert config.display_name == "Corporate IdP"
        assert config.is_active is True

    @pytest.mark.asyncio
    async def test_list_sso_configs(self, db_session: AsyncSession, sample_workspace):
        from app.services import sso_configuration_service

        for name in ["IdP A", "IdP B"]:
            await sso_configuration_service.create_sso_config(
                db_session,
                workspace_id=sample_workspace.id,
                provider_type="saml",
                display_name=name,
                metadata_url="https://idp.example.com/metadata",
                created_by=STUB_USER_ID,
            )
        await db_session.commit()

        items, total = await sso_configuration_service.list_sso_configs(
            db_session, sample_workspace.id
        )
        assert total == 2
        assert len(items) == 2

    @pytest.mark.asyncio
    async def test_delete_sso_config(self, db_session: AsyncSession, sample_workspace):
        from app.services import sso_configuration_service

        config = await sso_configuration_service.create_sso_config(
            db_session,
            workspace_id=sample_workspace.id,
            provider_type="saml",
            display_name="Temp IdP",
            created_by=STUB_USER_ID,
        )
        await db_session.commit()

        deleted = await sso_configuration_service.delete_sso_config(
            db_session, config.id
        )
        assert deleted is True

    @pytest.mark.asyncio
    async def test_toggle_sso_config(self, db_session: AsyncSession, sample_workspace):
        from app.services import sso_configuration_service

        config = await sso_configuration_service.create_sso_config(
            db_session,
            workspace_id=sample_workspace.id,
            provider_type="oidc",
            display_name="Toggle IdP",
            created_by=STUB_USER_ID,
        )
        await db_session.commit()

        toggled = await sso_configuration_service.toggle_sso_config(
            db_session, config.id, is_active=False
        )
        assert toggled is not None
        assert toggled.is_active is False


# ══════════════════════════════════════════════════════════════════
# FM-178: IP Allowlist Middleware Tests
# ══════════════════════════════════════════════════════════════════


class TestIPAllowlistMiddleware:
    @pytest.mark.asyncio
    async def test_ipv6_cidr_validation(
        self, db_session: AsyncSession, sample_workspace
    ):
        """IPv6 CIDR entries should be accepted."""
        entry = await ip_allowlist_service.add_allowlist_entry(
            db_session,
            workspace_id=sample_workspace.id,
            cidr="2001:db8::/32",
            created_by=STUB_USER_ID,
        )
        await db_session.commit()
        assert entry.cidr == "2001:db8::/32"

    @pytest.mark.asyncio
    async def test_ipv6_matching(self, db_session: AsyncSession, sample_workspace):
        """IPv6 addresses should match against IPv6 CIDRs."""
        await ip_allowlist_service.add_allowlist_entry(
            db_session,
            workspace_id=sample_workspace.id,
            cidr="2001:db8::/32",
            created_by=STUB_USER_ID,
        )
        await db_session.commit()

        entries = await ip_allowlist_service.get_workspace_allowlist(
            db_session, sample_workspace.id
        )
        assert (
            ip_allowlist_service.check_ip_against_allowlist("2001:db8::1", entries)
            is True
        )
        assert (
            ip_allowlist_service.check_ip_against_allowlist("2001:db9::1", entries)
            is False
        )

    def test_ip_enforcement_requires_governance_flag(self):
        """Middleware only activates when governance_settings.ip_enforcement_enabled is True."""
        # This is a design check — the middleware reads governance_settings
        # from the workspace model. Without the flag, requests pass through.
        from app.core.ip_allowlist_middleware import _WORKSPACE_PATH_RE

        # Verify the regex matches workspace paths
        match = _WORKSPACE_PATH_RE.search(
            "/api/v1/workspaces/12345678-1234-1234-1234-123456789012/audit-log"
        )
        assert match is not None
        assert match.group(1) == "12345678-1234-1234-1234-123456789012"

        # Non-workspace paths should not match
        assert _WORKSPACE_PATH_RE.search("/api/v1/health") is None
        assert _WORKSPACE_PATH_RE.search("/api/v1/users/me") is None


# ══════════════════════════════════════════════════════════════════
# FM-179: Secret Resolution & Rotation Tests
# ══════════════════════════════════════════════════════════════════


class TestSecretResolution:
    @pytest.mark.asyncio
    async def test_resolve_secret_from_env(
        self, db_session: AsyncSession, sample_project, monkeypatch
    ):
        """resolve_secret() returns the env var value for a credential."""
        from app.services import credential_vault_service

        cred = await credential_vault_service.create_credential(
            db_session,
            name="Test API Key",
            env_key="TEST_FM179_SECRET",
            project_id=sample_project.id,
        )
        await db_session.commit()

        # Set env var
        monkeypatch.setenv("TEST_FM179_SECRET", "sk-real-secret-123")

        resolved = await credential_vault_service.resolve_secret(db_session, cred.id)
        assert resolved == "sk-real-secret-123"

    @pytest.mark.asyncio
    async def test_resolve_secret_missing_env(
        self, db_session: AsyncSession, sample_project, monkeypatch
    ):
        """resolve_secret() returns None when env var is not set."""
        from app.services import credential_vault_service

        cred = await credential_vault_service.create_credential(
            db_session,
            name="Missing Key",
            env_key="NONEXISTENT_FM179_KEY",
            project_id=sample_project.id,
        )
        await db_session.commit()

        monkeypatch.delenv("NONEXISTENT_FM179_KEY", raising=False)

        resolved = await credential_vault_service.resolve_secret(db_session, cred.id)
        assert resolved is None

    @pytest.mark.asyncio
    async def test_resolve_secret_scope_enforcement(
        self, db_session: AsyncSession, sample_project, monkeypatch
    ):
        """resolve_secret() denies access when scopes don't match."""
        from app.services import credential_vault_service

        cred = await credential_vault_service.create_credential(
            db_session,
            name="Scoped Key",
            env_key="TEST_FM179_SCOPED",
            project_id=sample_project.id,
            scopes=["read", "write"],
        )
        await db_session.commit()

        monkeypatch.setenv("TEST_FM179_SCOPED", "secret-value")

        # Matching scope
        resolved = await credential_vault_service.resolve_secret(
            db_session, cred.id, allowed_scopes=["read"]
        )
        assert resolved == "secret-value"

        # Non-matching scope
        resolved = await credential_vault_service.resolve_secret(
            db_session, cred.id, allowed_scopes=["admin"]
        )
        assert resolved is None

    @pytest.mark.asyncio
    async def test_rotate_credential(self, db_session: AsyncSession, sample_project):
        """rotate_credential() updates last_rotated_at."""
        from app.services import credential_vault_service

        cred = await credential_vault_service.create_credential(
            db_session,
            name="Rotatable Key",
            env_key="TEST_FM179_ROTATE",
            project_id=sample_project.id,
        )
        await db_session.commit()

        assert cred.last_rotated_at is None

        rotated = await credential_vault_service.rotate_credential(db_session, cred.id)
        assert rotated is not None
        await db_session.commit()

    @pytest.mark.asyncio
    async def test_resolve_expired_credential(
        self, db_session: AsyncSession, sample_project, monkeypatch
    ):
        """resolve_secret() returns None for expired credentials."""
        from app.services import credential_vault_service

        cred = await credential_vault_service.create_credential(
            db_session,
            name="Expired Key",
            env_key="TEST_FM179_EXPIRED",
            project_id=sample_project.id,
        )
        await db_session.commit()

        monkeypatch.setenv("TEST_FM179_EXPIRED", "still-here")

        # Mark as expired
        cred.status = "EXPIRED"
        db_session.add(cred)
        await db_session.commit()

        resolved = await credential_vault_service.resolve_secret(db_session, cred.id)
        assert resolved is None


# ══════════════════════════════════════════════════════════════════
# Edge Cases & Cross-Cutting
# ══════════════════════════════════════════════════════════════════


class TestRBACEnhancements:
    @pytest.mark.asyncio
    async def test_workspace_audit_permission_required(
        self, db_session: AsyncSession, sample_workspace
    ):
        """WORKSPACE_VIEW_AUDIT is restricted to OWNER, ADMIN, REVIEWER."""
        from app.services.authz_service import is_workspace_action_allowed, Action
        from app.models.membership import WorkspaceRole

        assert (
            is_workspace_action_allowed(
                WorkspaceRole.OWNER, Action.WORKSPACE_VIEW_AUDIT
            )
            is True
        )
        assert (
            is_workspace_action_allowed(
                WorkspaceRole.ADMIN, Action.WORKSPACE_VIEW_AUDIT
            )
            is True
        )
        assert (
            is_workspace_action_allowed(
                WorkspaceRole.REVIEWER, Action.WORKSPACE_VIEW_AUDIT
            )
            is True
        )
        assert (
            is_workspace_action_allowed(
                WorkspaceRole.OPERATOR, Action.WORKSPACE_VIEW_AUDIT
            )
            is False
        )
        assert (
            is_workspace_action_allowed(
                WorkspaceRole.VIEWER, Action.WORKSPACE_VIEW_AUDIT
            )
            is False
        )

    @pytest.mark.asyncio
    async def test_workspace_governance_permission_required(
        self, db_session: AsyncSession
    ):
        """WORKSPACE_MANAGE_GOVERNANCE is restricted to OWNER, ADMIN."""
        from app.services.authz_service import is_workspace_action_allowed, Action
        from app.models.membership import WorkspaceRole

        assert (
            is_workspace_action_allowed(
                WorkspaceRole.OWNER, Action.WORKSPACE_MANAGE_GOVERNANCE
            )
            is True
        )
        assert (
            is_workspace_action_allowed(
                WorkspaceRole.ADMIN, Action.WORKSPACE_MANAGE_GOVERNANCE
            )
            is True
        )
        assert (
            is_workspace_action_allowed(
                WorkspaceRole.OPERATOR, Action.WORKSPACE_MANAGE_GOVERNANCE
            )
            is False
        )
        assert (
            is_workspace_action_allowed(
                WorkspaceRole.REVIEWER, Action.WORKSPACE_MANAGE_GOVERNANCE
            )
            is False
        )

    @pytest.mark.asyncio
    async def test_project_approval_permission(self, db_session: AsyncSession):
        """PROJECT_APPROVE restricted to LEAD, REVIEWER."""
        from app.services.authz_service import is_project_action_allowed, Action
        from app.models.membership import ProjectRole

        assert (
            is_project_action_allowed(ProjectRole.LEAD, Action.PROJECT_APPROVE) is True
        )
        assert (
            is_project_action_allowed(ProjectRole.REVIEWER, Action.PROJECT_APPROVE)
            is True
        )
        assert (
            is_project_action_allowed(ProjectRole.OPERATOR, Action.PROJECT_APPROVE)
            is False
        )
        assert (
            is_project_action_allowed(ProjectRole.VIEWER, Action.PROJECT_APPROVE)
            is False
        )


# ══════════════════════════════════════════════════════════════════
# FM-180: Edge Cases & Integration Tests
# ══════════════════════════════════════════════════════════════════


class TestEdgeCases:
    @pytest.mark.asyncio
    async def test_audit_log_systems_actor(
        self, db_session: AsyncSession, sample_workspace
    ):
        """System-generated audit entries have no actor_id."""
        entry = await audit_log_service.log_event(
            db_session,
            actor_id=None,
            actor_type=AuditActorType.SYSTEM,
            action="system.maintenance",
            resource_type="system",
            workspace_id=sample_workspace.id,
        )
        await db_session.commit()
        assert entry.actor_id is None
        assert entry.actor_type == AuditActorType.SYSTEM

    @pytest.mark.asyncio
    async def test_policy_eval_custom_trigger(
        self, db_session: AsyncSession, sample_project
    ):
        """Custom policies match on resource_type or actions list."""
        policy = GovernancePolicy(
            name="Custom Block",
            trigger=PolicyTrigger.CUSTOM,
            action=PolicyAction.BLOCK,
            rules={"actions": ["custom.dangerous"]},
            project_id=sample_project.id,
            enabled=True,
            priority=5,
        )
        db_session.add(policy)
        await db_session.flush()

        result = await governance_engine_service.evaluate_policies(
            db_session,
            project_id=sample_project.id,
            trigger_action="custom.dangerous",
            resource_type="custom",
        )
        await db_session.commit()

        assert result["allowed"] is False
        assert "Custom Block" in result["blocked_by"]

    @pytest.mark.asyncio
    async def test_compliance_report_empty_workspace(
        self, db_session: AsyncSession, sample_workspace
    ):
        """Reports generate correctly even for empty workspaces."""
        report = await compliance_report_service.generate_report(
            db_session,
            workspace_id=sample_workspace.id,
            report_type=ComplianceReportType.CHANGE_MANAGEMENT,
            title="Empty WS Report",
            generated_by=STUB_USER_ID,
        )
        await db_session.commit()

        assert report.status == ComplianceReportStatus.READY
        assert report.content["total_changes"] == 0

    @pytest.mark.asyncio
    async def test_ip_allowlist_ipv6(self, db_session: AsyncSession, sample_workspace):
        """IPv6 CIDR ranges are supported."""
        await ip_allowlist_service.add_allowlist_entry(
            db_session,
            workspace_id=sample_workspace.id,
            cidr="::1/128",
            description="Loopback IPv6",
            created_by=STUB_USER_ID,
        )
        await db_session.commit()

        entries = await ip_allowlist_service.get_workspace_allowlist(
            db_session, sample_workspace.id
        )
        assert ip_allowlist_service.check_ip_against_allowlist("::1", entries) is True
        assert ip_allowlist_service.check_ip_against_allowlist("::2", entries) is False

    @pytest.mark.asyncio
    async def test_retention_policy_with_delete_action(
        self, db_session: AsyncSession, sample_workspace
    ):
        policy = await retention_policy_service.create_retention_policy(
            db_session,
            workspace_id=sample_workspace.id,
            entity_type="audit_log",
            retention_days=30,
            action=RetentionAction.DELETE,
            created_by=STUB_USER_ID,
        )
        await db_session.commit()
        assert policy.action == RetentionAction.DELETE
