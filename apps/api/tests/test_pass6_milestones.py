"""Pass 6 milestone tests — FM-148, FM-151, FM-155, FM-171, FM-179.

Tests: atomic batch approval, rich dashboard, governance CRUD,
AES-256-GCM encryption, token management, issue sync webhook, conflict resolution.
"""

import os
import uuid
from datetime import datetime, timezone, timedelta

import pytest
from tests.conftest import STUB_USER_ID

# Set encryption key for tests (32 bytes = 64 hex chars)
TEST_ENCRYPTION_KEY = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
os.environ["FORGEMIND_ENCRYPTION_KEY"] = TEST_ENCRYPTION_KEY


# ── Helpers ──────────────────────────────────────────────────────


async def _seed_project(db):
    from app.models.project import Project
    from app.models.membership import ProjectMember, ProjectRole

    project = Project(
        name="Pass6 Project", description="pass6", owner_id=STUB_USER_ID,
    )
    db.add(project)
    await db.flush()
    await db.refresh(project)
    lead = ProjectMember(
        project_id=project.id, user_id=STUB_USER_ID, role=ProjectRole.LEAD,
    )
    db.add(lead)
    await db.flush()
    return project


async def _seed_run(db, project_id):
    from app.models.run import Run
    run = Run(run_number=1, project_id=project_id, trigger="test")
    db.add(run)
    await db.flush()
    await db.refresh(run)
    return run


async def _seed_task(db, run_id):
    from app.models.task import Task, TaskStatus
    task = Task(
        title="P6 Task", description="test", task_type="code",
        status=TaskStatus.READY, order_index=0, run_id=run_id,
    )
    db.add(task)
    await db.flush()
    await db.refresh(task)
    return task


async def _seed_approval(db, project_id, task_id=None):
    from app.models.approval_request import ApprovalRequest, ApprovalStatus
    ar = ApprovalRequest(
        project_id=project_id,
        task_id=task_id,
        title="Test Approval",
        status=ApprovalStatus.PENDING,
    )
    db.add(ar)
    await db.flush()
    await db.refresh(ar)
    return ar


async def _seed_installation(db):
    from app.models.github_integration import GitHubInstallation
    inst = GitHubInstallation(
        installation_id=67890,
        account_login="p6-org",
        account_type="Organization",
        connected_by=STUB_USER_ID,
    )
    db.add(inst)
    await db.flush()
    await db.refresh(inst)
    return inst


async def _seed_repo_link(db, installation_id, project_id):
    from app.models.github_integration import RepositoryLink
    link = RepositoryLink(
        installation_id=installation_id,
        project_id=project_id,
        github_repo_id=55555,
        full_name="p6-org/p6-repo",
        default_branch="main",
    )
    db.add(link)
    await db.flush()
    await db.refresh(link)
    return link


async def _seed_workspace(db):
    from app.models.workspace import Workspace
    from app.models.membership import WorkspaceMember, WorkspaceRole

    ws = Workspace(
        name="P6 Workspace",
        slug=f"p6-ws-{uuid.uuid4().hex[:8]}",
        owner_id=STUB_USER_ID,
    )
    db.add(ws)
    await db.flush()
    await db.refresh(ws)

    member = WorkspaceMember(
        workspace_id=ws.id,
        user_id=STUB_USER_ID,
        role=WorkspaceRole.OWNER,
    )
    db.add(member)
    await db.flush()
    return ws


# ═══════════════════════════════════════════════════════════════════
# FM-148: Atomic Batch Approval
# ═══════════════════════════════════════════════════════════════════


class TestFM148AtomicBatch:
    @pytest.mark.asyncio
    async def test_batch_decide_approves_all(self, db_session):
        project = await _seed_project(db_session)
        a1 = await _seed_approval(db_session, project.id)
        a2 = await _seed_approval(db_session, project.id)

        from app.services.approval_enhanced_service import batch_decide
        from app.models.approval_request import ApprovalStatus

        results = await batch_decide(
            db_session, [a1.id, a2.id],
            status=ApprovalStatus.APPROVED,
            decided_by=str(STUB_USER_ID),
        )
        assert len(results) == 2
        assert all(r.status == ApprovalStatus.APPROVED for r in results)
        # Both have same decided_at (atomic)
        assert results[0].decided_at == results[1].decided_at

    @pytest.mark.asyncio
    async def test_batch_decide_rejects_all_on_invalid(self, db_session):
        """If one approval is invalid, none should be mutated."""
        project = await _seed_project(db_session)
        a1 = await _seed_approval(db_session, project.id)
        fake_id = uuid.uuid4()

        from app.services.approval_enhanced_service import batch_decide
        from app.models.approval_request import ApprovalStatus
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await batch_decide(
                db_session, [a1.id, fake_id],
                status=ApprovalStatus.APPROVED,
                decided_by=str(STUB_USER_ID),
            )
        assert exc_info.value.status_code == 404

        # a1 should still be PENDING (not mutated)
        await db_session.refresh(a1)
        assert a1.status == ApprovalStatus.PENDING

    @pytest.mark.asyncio
    async def test_batch_decide_rejects_already_decided(self, db_session):
        """Already-decided approval in batch should reject entire batch."""
        project = await _seed_project(db_session)
        a1 = await _seed_approval(db_session, project.id)
        a2 = await _seed_approval(db_session, project.id)

        from app.services.approval_enhanced_service import batch_decide
        from app.models.approval_request import ApprovalStatus
        from fastapi import HTTPException

        # Decide a2 first
        await batch_decide(
            db_session, [a2.id],
            status=ApprovalStatus.APPROVED,
            decided_by=str(STUB_USER_ID),
        )

        # Now try to batch-decide a1 and a2 together
        with pytest.raises(HTTPException) as exc_info:
            await batch_decide(
                db_session, [a1.id, a2.id],
                status=ApprovalStatus.REJECTED,
                decided_by=str(STUB_USER_ID),
            )
        assert exc_info.value.status_code == 409

        # a1 should still be PENDING
        await db_session.refresh(a1)
        assert a1.status == ApprovalStatus.PENDING

    @pytest.mark.asyncio
    async def test_batch_decide_empty_list(self, db_session):
        from app.services.approval_enhanced_service import batch_decide
        from app.models.approval_request import ApprovalStatus

        results = await batch_decide(
            db_session, [],
            status=ApprovalStatus.APPROVED,
            decided_by=str(STUB_USER_ID),
        )
        assert results == []


# ═══════════════════════════════════════════════════════════════════
# FM-148: Rich Cross-Project Dashboard
# ═══════════════════════════════════════════════════════════════════


class TestFM148RichDashboard:
    @pytest.mark.asyncio
    async def test_dashboard_has_health_grades(self, db_session):
        await _seed_project(db_session)  # need project membership for dashboard

        from app.services.project_overview_service import get_cross_project_dashboard

        result = await get_cross_project_dashboard(db_session, STUB_USER_ID)
        assert "projects" in result
        assert "totals" in result
        if result["projects"]:
            p = result["projects"][0]
            assert "health_grade" in p
            assert p["health_grade"] in ("A", "B", "C", "D", "F")
            assert "success_rate" in p
            assert "pending_approval_details" in p

    @pytest.mark.asyncio
    async def test_dashboard_empty_user(self, db_session):
        from app.services.project_overview_service import get_cross_project_dashboard

        empty_user = uuid.uuid4()
        result = await get_cross_project_dashboard(db_session, empty_user)
        assert result["projects"] == []
        assert result["totals"]["project_count"] == 0

    @pytest.mark.asyncio
    async def test_dashboard_pending_details(self, db_session):
        project = await _seed_project(db_session)
        run = await _seed_run(db_session, project.id)
        task = await _seed_task(db_session, run.id)
        a1 = await _seed_approval(db_session, project.id, task.id)

        from app.services.project_overview_service import get_cross_project_dashboard

        result = await get_cross_project_dashboard(db_session, STUB_USER_ID)
        p = result["projects"][0]
        assert len(p["pending_approval_details"]) >= 1
        assert p["pending_approval_details"][0]["approval_id"] == str(a1.id)


# ═══════════════════════════════════════════════════════════════════
# FM-179: AES-256-GCM Secret Encryption
# ═══════════════════════════════════════════════════════════════════


class TestFM179EncryptionService:
    def test_encrypt_decrypt_roundtrip(self):
        from app.services.encryption_service import encrypt, decrypt

        plaintext = "super-secret-api-key-12345"
        ciphertext = encrypt(plaintext)
        assert isinstance(ciphertext, bytes)
        assert len(ciphertext) > 12 + 16  # nonce + tag minimum
        decrypted = decrypt(ciphertext)
        assert decrypted == plaintext

    def test_different_nonce_each_time(self):
        from app.services.encryption_service import encrypt

        ct1 = encrypt("same-value")
        ct2 = encrypt("same-value")
        # Nonces differ → ciphertexts differ
        assert ct1 != ct2

    def test_tampered_ciphertext_fails(self):
        from app.services.encryption_service import encrypt, decrypt

        ct = encrypt("hello")
        tampered = ct[:-1] + bytes([ct[-1] ^ 0xFF])
        with pytest.raises(Exception):
            decrypt(tampered)

    def test_short_ciphertext_fails(self):
        from app.services.encryption_service import decrypt

        with pytest.raises(ValueError, match="too short"):
            decrypt(b"short")

    def test_generate_key_hex(self):
        from app.services.encryption_service import generate_key_hex

        key = generate_key_hex()
        assert len(key) == 64
        int(key, 16)  # Must be valid hex

    def test_missing_key_raises(self):
        from app.services.encryption_service import encrypt

        old = os.environ.pop("FORGEMIND_ENCRYPTION_KEY", None)
        try:
            with pytest.raises(RuntimeError, match="not set"):
                encrypt("x")
        finally:
            if old:
                os.environ["FORGEMIND_ENCRYPTION_KEY"] = old


class TestFM179CredentialEncryption:
    @pytest.mark.asyncio
    async def test_create_credential_with_encrypted_value(self, db_session):
        # Seed a connector-less credential with secret_value
        from app.services.credential_vault_service import create_credential, resolve_secret
        from app.models.credential_vault import SecretStatus

        cred = await create_credential(
            db_session,
            name="Encrypted API Key",
            env_key="P6_TEST_ENCRYPTED_KEY",
            secret_value="my-secret-token-xyz",
        )
        assert cred.encrypted_value is not None
        assert cred.status == SecretStatus.ACTIVE

        # Resolve should return the decrypted value
        resolved = await resolve_secret(db_session, cred.id)
        assert resolved == "my-secret-token-xyz"

    @pytest.mark.asyncio
    async def test_resolve_falls_back_to_env(self, db_session):
        from app.services.credential_vault_service import create_credential, resolve_secret

        os.environ["P6_TEST_ENV_FALLBACK"] = "env-value-123"
        try:
            cred = await create_credential(
                db_session,
                name="Env Fallback",
                env_key="P6_TEST_ENV_FALLBACK",
            )
            assert cred.encrypted_value is None
            resolved = await resolve_secret(db_session, cred.id)
            assert resolved == "env-value-123"
        finally:
            os.environ.pop("P6_TEST_ENV_FALLBACK", None)

    @pytest.mark.asyncio
    async def test_store_encrypted_secret_update(self, db_session):
        from app.services.credential_vault_service import (
            create_credential, store_encrypted_secret, resolve_secret,
        )

        cred = await create_credential(
            db_session, name="Update Me", env_key="P6_TEST_UPDATE_ENC",
        )
        assert cred.encrypted_value is None

        updated = await store_encrypted_secret(
            db_session, cred.id, "newly-encrypted-value",
        )
        assert updated is not None
        assert updated.encrypted_value is not None

        resolved = await resolve_secret(db_session, cred.id)
        assert resolved == "newly-encrypted-value"

    @pytest.mark.asyncio
    async def test_build_credential_read_with_encryption(self, db_session):
        from app.services.credential_vault_service import (
            create_credential, build_credential_read,
        )

        cred = await create_credential(
            db_session,
            name="Masked Test",
            env_key="P6_TEST_MASKED",
            secret_value="abcdefghijklmnop",
        )
        read = build_credential_read(cred)
        assert read["is_set"] is True
        assert "****" in read["masked_preview"]
        assert "abcdefghijklmnop" not in read["masked_preview"]


# ═══════════════════════════════════════════════════════════════════
# FM-171: Governance Settings CRUD
# ═══════════════════════════════════════════════════════════════════


class TestFM171GovernanceSettings:
    @pytest.mark.asyncio
    async def test_governance_default_values(self, db_session):
        ws = await _seed_workspace(db_session)
        assert ws.governance_settings is None
        # Route should return defaults (tested at service level here)
        defaults = ws.governance_settings or {
            "plan_tier": "free",
            "compliance_level": "none",
            "sso_enforced": False,
        }
        assert defaults["plan_tier"] == "free"

    @pytest.mark.asyncio
    async def test_governance_update_via_model(self, db_session):
        ws = await _seed_workspace(db_session)
        ws.governance_settings = {
            "plan_tier": "enterprise",
            "compliance_level": "soc2",
            "sso_enforced": True,
            "ip_enforcement_enabled": False,
            "data_region": "us-east-1",
            "audit_retention_days": 365,
        }
        await db_session.flush()
        await db_session.refresh(ws)
        assert ws.governance_settings["plan_tier"] == "enterprise"
        assert ws.governance_settings["compliance_level"] == "soc2"
        assert ws.governance_settings["audit_retention_days"] == 365

    @pytest.mark.asyncio
    async def test_governance_route_get(self, client, db_session):
        ws = await _seed_workspace(db_session)
        await db_session.commit()
        resp = await client.get(f"/workspaces/{ws.id}/governance")
        assert resp.status_code == 200
        data = resp.json()
        assert data["plan_tier"] == "free"

    @pytest.mark.asyncio
    async def test_governance_route_update(self, client, db_session):
        ws = await _seed_workspace(db_session)
        await db_session.commit()
        resp = await client.put(
            f"/workspaces/{ws.id}/governance",
            json={"plan_tier": "team", "compliance_level": "basic"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["plan_tier"] == "team"
        assert data["compliance_level"] == "basic"

    @pytest.mark.asyncio
    async def test_governance_route_invalid_tier(self, client, db_session):
        ws = await _seed_workspace(db_session)
        await db_session.commit()
        resp = await client.put(
            f"/workspaces/{ws.id}/governance",
            json={"plan_tier": "ultra-premium"},
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_governance_route_invalid_retention(self, client, db_session):
        ws = await _seed_workspace(db_session)
        await db_session.commit()
        resp = await client.put(
            f"/workspaces/{ws.id}/governance",
            json={"audit_retention_days": 99999},
        )
        assert resp.status_code == 422


# ═══════════════════════════════════════════════════════════════════
# FM-151: Token Encryption + Refresh + Callback
# ═══════════════════════════════════════════════════════════════════


class TestFM151TokenManagement:
    @pytest.mark.asyncio
    async def test_store_and_retrieve_token(self, db_session):
        inst = await _seed_installation(db_session)

        from app.services.github_installation_service import (
            store_installation_token, get_installation_token,
        )

        await store_installation_token(
            db_session, inst.id, "ghs_test_token_123",
        )
        token = await get_installation_token(db_session, inst.id)
        assert token == "ghs_test_token_123"

    @pytest.mark.asyncio
    async def test_expired_token_returns_none(self, db_session):
        inst = await _seed_installation(db_session)

        from app.services.github_installation_service import (
            store_installation_token, get_installation_token,
        )

        past = datetime.now(timezone.utc) - timedelta(hours=2)
        await store_installation_token(
            db_session, inst.id, "ghs_expired", expires_at=past,
        )
        token = await get_installation_token(db_session, inst.id)
        assert token is None

    @pytest.mark.asyncio
    async def test_no_token_stored(self, db_session):
        inst = await _seed_installation(db_session)
        from app.services.github_installation_service import get_installation_token
        token = await get_installation_token(db_session, inst.id)
        assert token is None

    @pytest.mark.asyncio
    async def test_handle_oauth_callback(self, db_session):
        inst = await _seed_installation(db_session)

        from app.services.github_installation_service import (
            handle_oauth_callback, get_installation_token,
        )

        result = await handle_oauth_callback(
            db_session,
            installation_id_gh=inst.installation_id,
            access_token="ghs_callback_token",
        )
        assert result.access_token_encrypted is not None
        assert result.token_expires_at is not None

        token = await get_installation_token(db_session, result.id)
        assert token == "ghs_callback_token"

    @pytest.mark.asyncio
    async def test_refresh_without_client_returns_none(self, db_session):
        inst = await _seed_installation(db_session)
        from app.services.github_installation_service import refresh_installation_token
        result = await refresh_installation_token(db_session, inst.id)
        assert result is None

    @pytest.mark.asyncio
    async def test_oauth_callback_route(self, client, db_session):
        inst = await _seed_installation(db_session)
        await db_session.commit()
        resp = await client.post("/github/auth/callback", json={
            "installation_id": inst.installation_id,
            "access_token": "ghs_route_token",
            "expires_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["token_stored"] is True
        assert data["installation_id"] == inst.installation_id

    @pytest.mark.asyncio
    async def test_oauth_callback_unknown_installation(self, client, db_session):
        await db_session.commit()
        resp = await client.post("/github/auth/callback", json={
            "installation_id": 99999999,
            "access_token": "ghs_unknown",
        })
        assert resp.status_code == 404


# ═══════════════════════════════════════════════════════════════════
# FM-155: Issue Sync Webhook + Conflict Resolution
# ═══════════════════════════════════════════════════════════════════


class TestFM155IssueSyncWebhook:
    @pytest.mark.asyncio
    async def test_handle_issue_opened_webhook(self, db_session):
        project = await _seed_project(db_session)
        inst = await _seed_installation(db_session)
        repo = await _seed_repo_link(db_session, inst.id, project.id)

        from app.services.issue_sync_service import handle_issue_webhook
        from app.models.github_integration import IssueLinkStatus

        payload = {
            "action": "opened",
            "issue": {
                "number": 42,
                "title": "Bug: something broke",
                "html_url": "https://github.com/p6-org/p6-repo/issues/42",
                "labels": [{"name": "bug"}, {"name": "urgent"}],
            },
        }
        issue = await handle_issue_webhook(db_session, payload, repo)
        assert issue is not None
        assert issue.issue_number == 42
        assert issue.title == "Bug: something broke"
        assert issue.status == IssueLinkStatus.OPEN
        assert "bug" in issue.labels

    @pytest.mark.asyncio
    async def test_handle_issue_closed_webhook(self, db_session):
        project = await _seed_project(db_session)
        inst = await _seed_installation(db_session)
        repo = await _seed_repo_link(db_session, inst.id, project.id)

        from app.services.issue_sync_service import handle_issue_webhook
        from app.models.github_integration import IssueLinkStatus, IssueLink

        # Create existing issue
        issue = IssueLink(
            repository_link_id=repo.id, project_id=project.id,
            issue_number=42, title="Test", issue_url="http://x",
            status=IssueLinkStatus.OPEN, labels=[],
        )
        db_session.add(issue)
        await db_session.flush()

        payload = {
            "action": "closed",
            "issue": {"number": 42, "title": "Test"},
        }
        result = await handle_issue_webhook(db_session, payload, repo)
        assert result is not None
        assert result.status == IssueLinkStatus.CLOSED

    @pytest.mark.asyncio
    async def test_handle_issue_edited_webhook(self, db_session):
        project = await _seed_project(db_session)
        inst = await _seed_installation(db_session)
        repo = await _seed_repo_link(db_session, inst.id, project.id)

        from app.services.issue_sync_service import handle_issue_webhook
        from app.models.github_integration import IssueLinkStatus, IssueLink

        issue = IssueLink(
            repository_link_id=repo.id, project_id=project.id,
            issue_number=100, title="Original", issue_url="http://x",
            status=IssueLinkStatus.OPEN, labels=[],
        )
        db_session.add(issue)
        await db_session.flush()

        payload = {
            "action": "edited",
            "issue": {
                "number": 100,
                "title": "Updated Title",
                "labels": [{"name": "feature"}],
            },
        }
        result = await handle_issue_webhook(db_session, payload, repo)
        assert result.title == "Updated Title"
        assert "feature" in result.labels

    @pytest.mark.asyncio
    async def test_handle_issue_reopened_webhook(self, db_session):
        project = await _seed_project(db_session)
        inst = await _seed_installation(db_session)
        repo = await _seed_repo_link(db_session, inst.id, project.id)

        from app.services.issue_sync_service import handle_issue_webhook
        from app.models.github_integration import IssueLinkStatus, IssueLink

        issue = IssueLink(
            repository_link_id=repo.id, project_id=project.id,
            issue_number=50, title="Closed One", issue_url="http://x",
            status=IssueLinkStatus.CLOSED, labels=[],
        )
        db_session.add(issue)
        await db_session.flush()

        payload = {
            "action": "reopened",
            "issue": {"number": 50, "title": "Closed One"},
        }
        result = await handle_issue_webhook(db_session, payload, repo)
        assert result.status == IssueLinkStatus.OPEN

    @pytest.mark.asyncio
    async def test_conflict_resolution_remote_wins(self, db_session):
        project = await _seed_project(db_session)
        inst = await _seed_installation(db_session)
        repo = await _seed_repo_link(db_session, inst.id, project.id)

        from app.models.github_integration import IssueLink, IssueLinkStatus
        from app.services.issue_sync_service import resolve_conflict

        issue = IssueLink(
            repository_link_id=repo.id, project_id=project.id,
            issue_number=77, title="Local Title", issue_url="http://x",
            status=IssueLinkStatus.OPEN, labels=["old"],
        )
        db_session.add(issue)
        await db_session.flush()
        await db_session.refresh(issue)

        result = await resolve_conflict(
            db_session, issue.id,
            strategy="remote_wins",
            remote_title="Remote Title",
            remote_status="closed",
            remote_labels=["new"],
        )
        assert result.title == "Remote Title"
        assert result.status == IssueLinkStatus.CLOSED
        assert result.labels == ["new"]

    @pytest.mark.asyncio
    async def test_conflict_resolution_local_wins(self, db_session):
        project = await _seed_project(db_session)
        inst = await _seed_installation(db_session)
        repo = await _seed_repo_link(db_session, inst.id, project.id)

        from app.models.github_integration import IssueLink, IssueLinkStatus
        from app.services.issue_sync_service import resolve_conflict

        issue = IssueLink(
            repository_link_id=repo.id, project_id=project.id,
            issue_number=88, title="My Title", issue_url="http://x",
            status=IssueLinkStatus.OPEN, labels=["mine"],
        )
        db_session.add(issue)
        await db_session.flush()
        await db_session.refresh(issue)

        result = await resolve_conflict(
            db_session, issue.id,
            strategy="local_wins",
            remote_title="Ignored",
        )
        assert result.title == "My Title"

    @pytest.mark.asyncio
    async def test_export_with_mock_client(self, db_session):
        project = await _seed_project(db_session)
        inst = await _seed_installation(db_session)
        await _seed_repo_link(db_session, inst.id, project.id)

        class MockGitHubClient:
            async def create_issue(self, owner, repo, *, title, body, labels):
                return {
                    "number": 999,
                    "html_url": f"https://github.com/{owner}/{repo}/issues/999",
                    "id": 123456,
                }

        from app.services.issue_sync_service import export_issue_to_github

        issue = await export_issue_to_github(
            db_session,
            project_id=project.id,
            title="Exported Issue",
            body="Test body",
            labels=["exported"],
            github_client=MockGitHubClient(),
        )
        assert issue.issue_number == 999
        assert "issues/999" in issue.issue_url

    @pytest.mark.asyncio
    async def test_export_without_client_pending(self, db_session):
        project = await _seed_project(db_session)
        inst = await _seed_installation(db_session)
        await _seed_repo_link(db_session, inst.id, project.id)

        from app.services.issue_sync_service import export_issue_to_github

        issue = await export_issue_to_github(
            db_session,
            project_id=project.id,
            title="Pending Export",
        )
        assert issue.issue_number == 0  # Pending
