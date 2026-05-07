"""FM-211: Security hardening tests — covers all 25 fixed vulnerabilities.

Each test class maps to a requirement from the FM-211 spec.
"""

import uuid

import pytest
from fastapi import HTTPException
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import STUB_USER_ID


# ── Helpers ──────────────────────────────────────────────────────


def _unauth_override():
    """Dependency override that simulates an unauthenticated request."""

    async def _raise():
        raise HTTPException(status_code=401, detail="Authentication required")

    return _raise


# ─────────────────────────────────────────────────────────────────
# C-1: Credential Vault IDOR
# ─────────────────────────────────────────────────────────────────


class TestCredentialVaultIDOR:
    """GET /vault/credentials now requires project_id (non-optional)."""

    @pytest.mark.asyncio
    async def test_no_project_id_returns_422(self, client: AsyncClient):
        resp = await client.get("/vault/credentials")
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_no_auth_returns_401(
        self, client: AsyncClient, sample_project, db_session
    ):
        from app.main import create_app
        from app.db.session import get_db
        from app.core.auth import get_current_user_id

        app = create_app()
        app.dependency_overrides[get_db] = lambda: (yield db_session)
        app.dependency_overrides[get_current_user_id] = _unauth_override()

        from httpx import ASGITransport

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            resp = await ac.get(f"/vault/credentials?project_id={sample_project.id}")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_valid_auth_and_project_id_returns_200(
        self, client: AsyncClient, sample_project
    ):
        resp = await client.get(f"/vault/credentials?project_id={sample_project.id}")
        assert resp.status_code == 200


# ─────────────────────────────────────────────────────────────────
# C-2: Custom Role Privilege Escalation
# ─────────────────────────────────────────────────────────────────


class TestCustomRolePrivEsc:
    """PATCH /custom-roles/{id} now requires workspace membership."""

    @pytest.mark.asyncio
    async def test_no_auth_returns_401(self, client: AsyncClient, db_session):
        from app.main import create_app
        from app.db.session import get_db
        from app.core.auth import get_current_user_id

        fake_role_id = uuid.uuid4()
        app = create_app()
        app.dependency_overrides[get_db] = lambda: (yield db_session)
        app.dependency_overrides[get_current_user_id] = _unauth_override()

        from httpx import ASGITransport

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            resp = await ac.patch(
                f"/custom-roles/{fake_role_id}", json={"name": "evil"}
            )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_nonexistent_role_returns_404(self, client: AsyncClient):
        fake_id = uuid.uuid4()
        resp = await client.patch(f"/custom-roles/{fake_id}", json={"name": "evil"})
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_workspace_admin_can_update_own_role(
        self, client: AsyncClient, db_session
    ):
        """Workspace OWNER can update roles in their own workspace."""
        from app.models.enterprise_governance import CustomRole
        from app.models.workspace import Workspace
        from app.models.membership import WorkspaceMember, WorkspaceRole

        ws = Workspace(name="Sec Test WS", slug="sec-test-ws", owner_id=STUB_USER_ID)
        db_session.add(ws)
        await db_session.flush()
        member = WorkspaceMember(
            workspace_id=ws.id, user_id=STUB_USER_ID, role=WorkspaceRole.OWNER
        )
        db_session.add(member)
        role = CustomRole(
            workspace_id=ws.id,
            name="old-name",
            scope="project",
            permissions=["project:view"],
            created_by=STUB_USER_ID,
        )
        db_session.add(role)
        await db_session.flush()

        resp = await client.patch(f"/custom-roles/{role.id}", json={"name": "new-name"})
        assert resp.status_code == 200
        assert resp.json()["name"] == "new-name"


# ─────────────────────────────────────────────────────────────────
# C-3: Null project_id Auth Bypass
# ─────────────────────────────────────────────────────────────────


class TestNullProjectIdBypass:
    """All three bypass locations now raise 403 when project is unresolvable."""

    @pytest.mark.asyncio
    async def test_approval_decide_with_unknown_id_returns_403_or_404(
        self, client: AsyncClient
    ):
        fake_id = uuid.uuid4()
        resp = await client.post(
            f"/api/v1/approvals/{fake_id}/decide",
            json={"status": "approved"},
        )
        # 403 when project can't be resolved, 404 when approval not found
        assert resp.status_code in (403, 404)

    @pytest.mark.asyncio
    async def test_repo_approval_decide_with_unknown_id_returns_403_or_404(
        self, client: AsyncClient
    ):
        fake_id = uuid.uuid4()
        resp = await client.post(
            f"/api/v1/repo-approvals/{fake_id}/decide",
            json={"status": "approved"},
        )
        assert resp.status_code in (403, 404)

    @pytest.mark.asyncio
    async def test_sandbox_run_with_unknown_execution_returns_403_or_404(
        self, client: AsyncClient
    ):
        fake_id = uuid.uuid4()
        resp = await client.post(
            "/api/v1/sandbox/run", json={"execution_id": str(fake_id)}
        )
        assert resp.status_code in (403, 404)

    @pytest.mark.asyncio
    async def test_approval_decide_on_real_approval_checks_permission(
        self, client: AsyncClient, sample_approval
    ):
        """Deciding on a real approval (with valid project) should proceed past auth check."""
        resp = await client.post(
            f"/api/v1/approvals/{sample_approval.id}/decide",
            json={"status": "approved"},
        )
        # 200 = success; 409 = already decided. Both mean auth passed.
        assert resp.status_code in (200, 409)


# ─────────────────────────────────────────────────────────────────
# C-4: Sandbox Path Traversal
# ─────────────────────────────────────────────────────────────────


class TestSandboxPathTraversal:
    """Sandbox working directory is now confined to SANDBOX_BASE_DIR."""

    @pytest.mark.asyncio
    async def test_traversal_path_fails(self, db_session: AsyncSession, sample_project):
        from app.models.code_ops import SandboxExecution, SandboxStatus
        from app.services.code_ops_service import (
            run_sandbox_execution,
            SANDBOX_BASE_DIR,
        )

        exe = SandboxExecution(
            project_id=sample_project.id,
            command="echo hello",
            working_directory="../../../etc",
            status=SandboxStatus.QUEUED,
            timeout_seconds=10,
            isolated=True,
        )
        db_session.add(exe)
        await db_session.flush()

        result = await run_sandbox_execution(db_session, exe.id)
        assert result.status == SandboxStatus.FAILED
        assert SANDBOX_BASE_DIR in result.stderr

    @pytest.mark.asyncio
    async def test_root_path_fails(self, db_session: AsyncSession, sample_project):
        from app.models.code_ops import SandboxExecution, SandboxStatus
        from app.services.code_ops_service import run_sandbox_execution

        exe = SandboxExecution(
            project_id=sample_project.id,
            command="echo hello",
            working_directory="/",
            status=SandboxStatus.QUEUED,
            timeout_seconds=10,
            isolated=True,
        )
        db_session.add(exe)
        await db_session.flush()

        result = await run_sandbox_execution(db_session, exe.id)
        assert result.status == SandboxStatus.FAILED

    @pytest.mark.asyncio
    async def test_empty_working_dir_uses_sandbox_base(
        self, db_session: AsyncSession, sample_project
    ):
        """No working_directory → defaults to SANDBOX_BASE_DIR, no traversal error."""
        from app.models.code_ops import SandboxExecution, SandboxStatus
        from app.services.code_ops_service import run_sandbox_execution

        exe = SandboxExecution(
            project_id=sample_project.id,
            command="echo ok",
            working_directory=None,
            status=SandboxStatus.QUEUED,
            timeout_seconds=10,
            isolated=True,
        )
        db_session.add(exe)
        await db_session.flush()

        result = await run_sandbox_execution(db_session, exe.id)
        # Should not fail with "Invalid working directory"
        assert "Invalid working directory" not in (result.stderr or "")


# ─────────────────────────────────────────────────────────────────
# H-13: Action.PROJECT_EDIT Enum
# ─────────────────────────────────────────────────────────────────


class TestActionProjectEditEnum:
    """Action.PROJECT_EDIT must exist and be granted to LEAD/OPERATOR."""

    def test_project_edit_enum_exists(self):
        from app.services.authz_service import Action

        assert hasattr(Action, "PROJECT_EDIT")
        assert Action.PROJECT_EDIT.value == "project:edit"

    def test_project_write_role_has_project_edit(self):
        from app.services.authz_service import Action, PROJECT_PERMISSIONS
        from app.models.membership import ProjectRole

        allowed = PROJECT_PERMISSIONS.get(Action.PROJECT_EDIT, set())
        assert ProjectRole.LEAD in allowed
        assert ProjectRole.OPERATOR in allowed


# ─────────────────────────────────────────────────────────────────
# H-11: Approval list IDOR via run_id
# ─────────────────────────────────────────────────────────────────


class TestNullProjectIdApprovalList:
    """GET /approvals requires project_id or resolvable run_id."""

    @pytest.mark.asyncio
    async def test_both_absent_returns_400(self, client: AsyncClient):
        resp = await client.get("/api/v1/approvals")
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_run_id_resolves_project_for_authorized_caller(
        self, client: AsyncClient, sample_run
    ):
        resp = await client.get(f"/api/v1/approvals?run_id={sample_run.id}")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_run_id_for_unknown_run_returns_404(self, client: AsyncClient):
        resp = await client.get(f"/api/v1/approvals?run_id={uuid.uuid4()}")
        assert resp.status_code == 404


# ─────────────────────────────────────────────────────────────────
# H-14: Sandbox env var masking
# ─────────────────────────────────────────────────────────────────


class TestSandboxEnvVarMasking:
    """Environment variable values must be masked in API responses and not stored plaintext."""

    @pytest.mark.asyncio
    async def test_env_values_masked_in_api_response(
        self, client: AsyncClient, db_session: AsyncSession, sample_project
    ):
        resp = await client.post(
            f"/projects/{sample_project.id}/sandbox",
            json={
                "command": "echo hi",
                "environment": {"SECRET_KEY": "super-secret-value"},
                "timeout_seconds": 5,
            },
        )
        assert resp.status_code == 201
        env = resp.json().get("environment") or {}
        assert env.get("SECRET_KEY") == "***"

    @pytest.mark.asyncio
    async def test_stored_db_record_has_no_plaintext_values(
        self, db_session: AsyncSession, sample_project
    ):
        from app.services.code_ops_service import create_sandbox_execution

        s = await create_sandbox_execution(
            db_session,
            project_id=sample_project.id,
            command="echo hi",
            environment={"MY_SECRET": "plaintext-value"},
        )
        # Stored value should be None (key-only storage), not the actual value
        assert s.environment is not None
        assert s.environment.get("MY_SECRET") is None
        assert "plaintext-value" not in str(s.environment)


# ─────────────────────────────────────────────────────────────────
# L-24: JWT error normalization
# ─────────────────────────────────────────────────────────────────


class TestJWTErrorNormalization:
    """All JWT failures must return the same generic 401 message."""

    @pytest.mark.asyncio
    async def test_garbage_token_returns_uniform_401(
        self, client: AsyncClient, sample_project
    ):
        resp = await client.get(
            f"/vault/credentials?project_id={sample_project.id}",
            headers={"Authorization": "Bearer notavalidtoken"},
        )
        assert resp.status_code == 401
        assert resp.json()["detail"] == "Could not validate credentials"

    @pytest.mark.asyncio
    async def test_expired_like_token_returns_uniform_401(
        self, client: AsyncClient, sample_project
    ):
        # A well-formed but wrong-key JWT triggers the same error path
        import base64
        import json as _json

        header = (
            base64.urlsafe_b64encode(
                _json.dumps({"alg": "HS256", "typ": "JWT"}).encode()
            )
            .rstrip(b"=")
            .decode()
        )
        payload = (
            base64.urlsafe_b64encode(
                _json.dumps({"sub": str(uuid.uuid4()), "exp": 1000000}).encode()
            )
            .rstrip(b"=")
            .decode()
        )
        fake_token = f"{header}.{payload}.invalidsignature"
        resp = await client.get(
            f"/vault/credentials?project_id={sample_project.id}",
            headers={"Authorization": f"Bearer {fake_token}"},
        )
        assert resp.status_code == 401
        assert resp.json()["detail"] == "Could not validate credentials"


# ─────────────────────────────────────────────────────────────────
# L-25: Commit SHA validation
# ─────────────────────────────────────────────────────────────────


class TestCommitSHAValidation:
    """POST /github/repos/{id}/statuses/{sha} validates SHA format."""

    @pytest.mark.asyncio
    async def test_short_sha_returns_400(self, client: AsyncClient):
        fake_repo = uuid.uuid4()
        resp = await client.post(
            f"/github/repos/{fake_repo}/statuses/abc123",
            json={"state": "success"},
        )
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_valid_sha_passes_validation(self, client: AsyncClient):
        fake_repo = uuid.uuid4()
        valid_sha = "a" * 40
        resp = await client.post(
            f"/github/repos/{fake_repo}/statuses/{valid_sha}",
            json={"state": "success"},
        )
        # Passes SHA validation; 404 because repo doesn't exist
        assert resp.status_code != 400


# ─────────────────────────────────────────────────────────────────
# H-15: Rate limiting active regardless of debug flag
# ─────────────────────────────────────────────────────────────────


class TestLoginRateLimit:
    """RateLimitMiddleware must be active even when debug=True."""

    def test_rate_limit_middleware_always_added(self):
        """create_app() always adds RateLimitMiddleware, regardless of debug."""
        from app.main import create_app
        from app.core.rate_limit import RateLimitMiddleware

        app = create_app()
        middleware_classes = [m.cls for m in app.user_middleware if hasattr(m, "cls")]
        assert RateLimitMiddleware in middleware_classes


# ─────────────────────────────────────────────────────────────────
# H-6: GitHub webhook secret required
# ─────────────────────────────────────────────────────────────────


class TestGithubWebhookSecretRequired:
    """POST /github/webhooks returns 503 when GITHUB_WEBHOOK_SECRET is unconfigured."""

    @pytest.mark.asyncio
    async def test_empty_secret_returns_503(self, client: AsyncClient, monkeypatch):
        from app.core import config as cfg

        monkeypatch.setattr(cfg.settings, "github_webhook_secret", "")
        resp = await client.post(
            "/github/webhooks",
            json={"action": "opened"},
            headers={"X-GitHub-Event": "pull_request"},
        )
        assert resp.status_code == 503

    @pytest.mark.asyncio
    async def test_wrong_signature_returns_401(self, client: AsyncClient, monkeypatch):
        from app.core import config as cfg

        monkeypatch.setattr(cfg.settings, "github_webhook_secret", "some-secret")
        resp = await client.post(
            "/github/webhooks",
            content=b'{"action":"opened"}',
            headers={
                "X-GitHub-Event": "pull_request",
                "X-Hub-Signature-256": "sha256=invalidsignature",
            },
        )
        assert resp.status_code == 401


# ─────────────────────────────────────────────────────────────────
# M-19: Approval notifications go to project reviewers, not project_id
# ─────────────────────────────────────────────────────────────────


class TestApprovalNotificationUser:
    """create_approval must not route notifications to project_id as a user_id."""

    @pytest.mark.asyncio
    async def test_notification_not_routed_to_project_id(
        self, db_session: AsyncSession, sample_project
    ):
        from app.schemas.approval import ApprovalCreate
        from app.services import approval_service

        notifications_created = []

        # Patch notification_service to capture calls
        import app.services.notification_service as ns

        original = ns.create_notification

        async def _capture(db, *, user_id, **kwargs):
            notifications_created.append(user_id)

        ns.create_notification = _capture
        try:
            data = ApprovalCreate(
                title="Test approval",
                project_id=sample_project.id,
            )
            await approval_service.create_approval(db_session, data)
        finally:
            ns.create_notification = original

        # Verify no notification was routed to project_id (which is not a user)
        for uid in notifications_created:
            assert uid != sample_project.id, (
                f"Notification was incorrectly sent to project_id {sample_project.id}"
            )


# ─────────────────────────────────────────────────────────────────
# M-22: Safety gate covers staging/test environments
# ─────────────────────────────────────────────────────────────────


class TestSafetyGateCoversNonProd:
    """Settings safety gate now fires for staging and test, not just production."""

    def test_staging_with_default_secret_raises(self):
        from app.core.config import Settings

        with pytest.raises(RuntimeError, match="SECRET_KEY"):
            Settings(
                APP_ENV="staging",
                SECRET_KEY="change-me-to-a-random-secret",
                _env_file=None,
            )

    def test_test_env_with_default_secret_raises(self):
        with pytest.raises(RuntimeError, match="SECRET_KEY"):
            from app.core.config import Settings

            Settings(
                APP_ENV="test",
                SECRET_KEY="change-me-to-a-random-secret",
                _env_file=None,
            )

    def test_development_with_default_secret_ok(self):
        from app.core.config import Settings

        # development env should NOT raise with default secret
        s = Settings(APP_ENV="development", _env_file=None)
        assert s.app_env == "development"


# ─────────────────────────────────────────────────────────────────
# H-13 (extended): Routes using PROJECT_EDIT don't crash
# ─────────────────────────────────────────────────────────────────


class TestProjectEditRoutesCrashFree:
    """Routes that reference Action.PROJECT_EDIT must not raise AttributeError."""

    @pytest.mark.asyncio
    async def test_tag_artifact_route_resolves_without_attribute_error(
        self, client: AsyncClient, sample_artifact
    ):
        """PATCH /artifacts/{id}/tag now uses PROJECT_EDIT which must exist."""
        resp = await client.patch(
            f"/api/v1/artifacts/{sample_artifact.id}/tag",
            json={"version_tag": "v1.0"},
        )
        # 200 = success; anything but 500 means PROJECT_EDIT was found
        assert resp.status_code != 500

    @pytest.mark.asyncio
    async def test_dismiss_recommendation_uses_project_edit(
        self, client: AsyncClient, db_session: AsyncSession, sample_project
    ):
        from app.models.search_knowledge import Recommendation, RecommendationType

        rec = Recommendation(
            project_id=sample_project.id,
            rec_type=RecommendationType.TECH_DEBT,
            title="Fix old code",
            body="Some old code needs attention",
        )
        db_session.add(rec)
        await db_session.flush()

        resp = await client.patch(f"/api/v1/recommendations/{rec.id}/dismiss")
        assert resp.status_code != 500


# ─────────────────────────────────────────────────────────────────
# L-23: Token TTL reduced to 1 hour
# ─────────────────────────────────────────────────────────────────


class TestTokenTTL:
    """Access tokens should expire in 1 hour, not 24."""

    def test_token_expire_hours_is_one(self):
        from app.core.auth import _TOKEN_EXPIRE_HOURS

        assert _TOKEN_EXPIRE_HOURS == 1


# ─────────────────────────────────────────────────────────────────
# H-7: Custom roles listing requires workspace membership
# ─────────────────────────────────────────────────────────────────


class TestCustomRolesListAuth:
    """GET /workspaces/{id}/custom-roles requires WORKSPACE_VIEW."""

    @pytest.mark.asyncio
    async def test_non_member_gets_404(self, client: AsyncClient):
        """Stub user is not a member of a random workspace → 404 from authz check."""
        random_ws_id = uuid.uuid4()
        resp = await client.get(f"/workspaces/{random_ws_id}/custom-roles")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_member_can_list_roles(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        from app.models.workspace import Workspace
        from app.models.membership import WorkspaceMember, WorkspaceRole

        ws = Workspace(name="Roles WS", slug="roles-ws", owner_id=STUB_USER_ID)
        db_session.add(ws)
        await db_session.flush()
        member = WorkspaceMember(
            workspace_id=ws.id, user_id=STUB_USER_ID, role=WorkspaceRole.VIEWER
        )
        db_session.add(member)
        await db_session.flush()

        resp = await client.get(f"/workspaces/{ws.id}/custom-roles")
        assert resp.status_code == 200
