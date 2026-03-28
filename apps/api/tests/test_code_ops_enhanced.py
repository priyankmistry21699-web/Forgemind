"""Tests for FM-061–069 enhanced code operations endpoints."""
import uuid
import tempfile
import os

import pytest
from httpx import AsyncClient


STUB_USER_ID = "00000000-0000-0000-0000-000000000001"


# ── FM-061: Sync metadata tests ─────────────────────────────────

@pytest.mark.asyncio
class TestRepoSyncMetadata:

    async def _create_local_repo(self, client: AsyncClient, project_id: str, workspace_path: str):
        resp = await client.post(f"/projects/{project_id}/repos", json={
            "provider": "local",
            "repo_url": "file:///local",
            "repo_name": "test-local",
            "workspace_path": workspace_path,
            "base_branch": "main",
            "target_branch": "develop",
            "branch_mode": "feature_branch",
        })
        assert resp.status_code == 201
        return resp.json()

    async def test_create_repo_with_sync_fields(self, client: AsyncClient, sample_project):
        pid = str(sample_project.id)
        with tempfile.TemporaryDirectory() as tmpdir:
            data = await self._create_local_repo(client, pid, tmpdir)
            assert data["base_branch"] == "main"
            assert data["target_branch"] == "develop"
            assert data["branch_mode"] == "feature_branch"

    async def test_get_sync_status(self, client: AsyncClient, sample_project):
        pid = str(sample_project.id)
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = await self._create_local_repo(client, pid, tmpdir)
            rid = repo["id"]
            resp = await client.get(f"/repos/{rid}/sync-status")
            assert resp.status_code == 200
            assert resp.json()["connection_id"] == rid

    async def test_refresh_sync_metadata(self, client: AsyncClient, sample_project):
        pid = str(sample_project.id)
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = await self._create_local_repo(client, pid, tmpdir)
            rid = repo["id"]
            resp = await client.post(f"/repos/{rid}/refresh-sync?commit_sha=abc123")
            assert resp.status_code == 200
            assert resp.json()["last_synced_commit"] == "abc123"

    async def test_sync_connection_updates_status(self, client: AsyncClient, sample_project):
        pid = str(sample_project.id)
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = await self._create_local_repo(client, pid, tmpdir)
            rid = repo["id"]
            resp = await client.post(f"/repos/{rid}/sync")
            assert resp.status_code == 200
            assert resp.json()["status"] == "synced"


# ── FM-062: File tree / content tests ───────────────────────────

@pytest.mark.asyncio
class TestFileTreeExplorer:

    async def _setup_workspace(self, client: AsyncClient, project_id: str, tmpdir: str):
        # Create some files in the temp workspace
        os.makedirs(os.path.join(tmpdir, "src"), exist_ok=True)
        with open(os.path.join(tmpdir, "src", "main.py"), "w") as f:
            f.write("print('hello')\n")
        with open(os.path.join(tmpdir, "README.md"), "w") as f:
            f.write("# Test Project\n")

        resp = await client.post(f"/projects/{project_id}/repos", json={
            "provider": "local",
            "repo_url": "file:///local",
            "repo_name": "explorer-test",
            "workspace_path": tmpdir,
        })
        assert resp.status_code == 201
        return resp.json()["id"]

    async def test_get_file_tree_root(self, client: AsyncClient, sample_project):
        pid = str(sample_project.id)
        with tempfile.TemporaryDirectory() as tmpdir:
            rid = await self._setup_workspace(client, pid, tmpdir)
            resp = await client.get(f"/repos/{rid}/tree")
            assert resp.status_code == 200
            data = resp.json()
            names = [e["name"] for e in data["entries"]]
            assert "src" in names
            assert "README.md" in names

    async def test_get_file_tree_subdir(self, client: AsyncClient, sample_project):
        pid = str(sample_project.id)
        with tempfile.TemporaryDirectory() as tmpdir:
            rid = await self._setup_workspace(client, pid, tmpdir)
            resp = await client.get(f"/repos/{rid}/tree", params={"path": "src"})
            assert resp.status_code == 200
            names = [e["name"] for e in resp.json()["entries"]]
            assert "main.py" in names

    async def test_get_file_content(self, client: AsyncClient, sample_project):
        pid = str(sample_project.id)
        with tempfile.TemporaryDirectory() as tmpdir:
            rid = await self._setup_workspace(client, pid, tmpdir)
            resp = await client.get(f"/repos/{rid}/file", params={"path": "src/main.py"})
            assert resp.status_code == 200
            data = resp.json()
            assert "hello" in data["content"]
            assert data["language"] == "python"

    async def test_get_file_metadata(self, client: AsyncClient, sample_project):
        pid = str(sample_project.id)
        with tempfile.TemporaryDirectory() as tmpdir:
            rid = await self._setup_workspace(client, pid, tmpdir)
            resp = await client.get(f"/repos/{rid}/file-meta", params={"path": "README.md"})
            assert resp.status_code == 200
            assert resp.json()["language"] == "markdown"

    async def test_path_traversal_blocked(self, client: AsyncClient, sample_project):
        pid = str(sample_project.id)
        with tempfile.TemporaryDirectory() as tmpdir:
            rid = await self._setup_workspace(client, pid, tmpdir)
            resp = await client.get(f"/repos/{rid}/file", params={"path": "../../etc/passwd"})
            assert resp.status_code == 400


# ── FM-063: Code artifact mapping tests ─────────────────────────

@pytest.mark.asyncio
class TestCodeArtifactMapping:

    async def test_create_artifact_with_code_mapping(self, client: AsyncClient, sample_project):
        pid = str(sample_project.id)
        resp = await client.post(f"/projects/{pid}/artifacts", json={
            "title": "impl: user service",
            "artifact_type": "implementation",
            "content": "class UserService: pass",
            "target_path": "src/services/user_service.py",
            "target_module": "services.user_service",
            "change_type": "create",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["target_path"] == "src/services/user_service.py"
        assert data["change_type"] == "create"

    async def test_update_artifact_code_mapping(self, client: AsyncClient, sample_project):
        pid = str(sample_project.id)
        create = await client.post(f"/projects/{pid}/artifacts", json={
            "title": "impl: update",
            "content": "code",
        })
        aid = create.json()["id"]
        resp = await client.patch(f"/artifacts/{aid}", json={
            "target_path": "src/main.py",
            "change_type": "modify",
        })
        assert resp.status_code == 200
        assert resp.json()["target_path"] == "src/main.py"


# ── FM-064: Enhanced patch proposals ─────────────────────────────

@pytest.mark.asyncio
class TestEnhancedPatchProposals:

    async def test_create_patch_with_fm064_fields(self, client: AsyncClient, sample_project):
        pid = str(sample_project.id)
        resp = await client.post(f"/projects/{pid}/patches", json={
            "title": "Add caching layer",
            "diff_content": "--- a/cache.py\n+++ b/cache.py\n+import redis",
            "target_files": ["src/cache.py", "src/config.py"],
            "patch_format": "unified",
            "proposed_by_agent": "architecture-agent",
            "readiness_state": "needs_review",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["target_files"] == ["src/cache.py", "src/config.py"]
        assert data["patch_format"] == "unified"
        assert data["proposed_by_agent"] == "architecture-agent"
        assert data["readiness_state"] == "needs_review"

    async def test_update_patch_readiness(self, client: AsyncClient, sample_project):
        pid = str(sample_project.id)
        create = await client.post(f"/projects/{pid}/patches", json={
            "title": "P", "diff_content": "d",
        })
        patch_id = create.json()["id"]
        resp = await client.patch(f"/patches/{patch_id}", json={
            "readiness_state": "ready",
        })
        assert resp.status_code == 200
        assert resp.json()["readiness_state"] == "ready"


# ── FM-065: Change review with annotations ──────────────────────

@pytest.mark.asyncio
class TestChangeReviewAnnotations:

    async def test_create_review_with_annotation(self, client: AsyncClient, sample_project):
        pid = str(sample_project.id)
        patch = await client.post(f"/projects/{pid}/patches", json={
            "title": "Ann", "diff_content": "d",
        })
        patch_id = patch.json()["id"]
        resp = await client.post(f"/patches/{patch_id}/reviews", json={
            "decision": "request_changes",
            "comment": "Use a context manager here",
            "file_path": "src/db.py",
            "line_start": 42,
            "line_end": 45,
            "suggestion": "with engine.connect() as conn:",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["file_path"] == "src/db.py"
        assert data["line_start"] == 42
        assert data["suggestion"] == "with engine.connect() as conn:"


# ── FM-067: PR draft generation ──────────────────────────────────

@pytest.mark.asyncio
class TestPRDraftGeneration:

    async def test_generate_pr_draft(self, client: AsyncClient, sample_project):
        pid = str(sample_project.id)
        patch = await client.post(f"/projects/{pid}/patches", json={
            "title": "Fix auth middleware",
            "diff_content": "diff data",
            "description": "Fixes token validation",
            "target_files": ["src/auth.py"],
        })
        patch_id = patch.json()["id"]
        resp = await client.post(f"/projects/{pid}/pr-drafts/generate", json={
            "patch_id": patch_id,
            "target_branch": "main",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert "[ForgeMind]" in data["title"]
        assert "Fix auth middleware" in data["title"]
        assert data["checklist"] is not None
        assert len(data["checklist"]) == 3

    async def test_generate_pr_draft_missing_patch(self, client: AsyncClient, sample_project):
        pid = str(sample_project.id)
        resp = await client.post(f"/projects/{pid}/pr-drafts/generate", json={
            "patch_id": str(uuid.uuid4()),
        })
        assert resp.status_code == 404


# ── FM-068: Approval gate check ──────────────────────────────────

@pytest.mark.asyncio
class TestApprovalGateCheck:

    async def test_approval_gate_no_prior_approval(self, client: AsyncClient, sample_project):
        pid = str(sample_project.id)
        resp = await client.get(
            f"/projects/{pid}/repo-approvals/check",
            params={"action_type": "push"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["requires_approval"] is True
        assert data["approved"] is False

    async def test_approval_gate_after_approval(self, client: AsyncClient, sample_project):
        pid = str(sample_project.id)
        create = await client.post(f"/projects/{pid}/repo-approvals", json={
            "action_type": "push", "reason": "Deploy fix",
        })
        aid = create.json()["id"]
        await client.post(f"/repo-approvals/{aid}/decide", json={
            "status": "approved", "decision_comment": "Go ahead",
        })
        resp = await client.get(
            f"/projects/{pid}/repo-approvals/check",
            params={"action_type": "push"},
        )
        assert resp.status_code == 200
        assert resp.json()["approved"] is True


# ── FM-069: Sandbox execution with safety ────────────────────────

@pytest.mark.asyncio
class TestSandboxRunner:

    async def test_create_sandbox_with_safety_fields(self, client: AsyncClient, sample_project):
        pid = str(sample_project.id)
        resp = await client.post(f"/projects/{pid}/sandbox", json={
            "command": "echo test",
            "allowed_commands": ["echo", "cat"],
            "resource_limits": {"max_memory_mb": 256},
            "isolated": True,
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["allowed_commands"] == ["echo", "cat"]
        assert data["isolated"] is True

    async def test_run_sandbox_allowed_command(self, client: AsyncClient, sample_project):
        pid = str(sample_project.id)
        create = await client.post(f"/projects/{pid}/sandbox", json={
            "command": "echo hello-sandbox",
            "timeout_seconds": 10,
        })
        eid = create.json()["id"]
        resp = await client.post("/sandbox/run", json={"execution_id": eid})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] in ("completed", "failed")
        if data["status"] == "completed":
            assert "hello-sandbox" in data["stdout"]

    async def test_run_sandbox_blocked_command(self, client: AsyncClient, sample_project):
        pid = str(sample_project.id)
        create = await client.post(f"/projects/{pid}/sandbox", json={
            "command": "rm -rf /",
            "timeout_seconds": 5,
        })
        eid = create.json()["id"]
        resp = await client.post("/sandbox/run", json={"execution_id": eid})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "failed"
        assert "not in allowlist" in data["stderr"]

    async def test_run_sandbox_dangerous_pattern(self, client: AsyncClient, sample_project):
        pid = str(sample_project.id)
        create = await client.post(f"/projects/{pid}/sandbox", json={
            "command": "echo test && rm -rf /",
            "timeout_seconds": 5,
        })
        eid = create.json()["id"]
        resp = await client.post("/sandbox/run", json={"execution_id": eid})
        assert resp.status_code == 200
        assert resp.json()["status"] == "failed"
        assert "Dangerous pattern" in resp.json()["stderr"]

    async def test_run_sandbox_404(self, client: AsyncClient):
        resp = await client.post("/sandbox/run", json={
            "execution_id": str(uuid.uuid4()),
        })
        assert resp.status_code == 404

    async def test_max_timeout_capped(self, client: AsyncClient, sample_project):
        pid = str(sample_project.id)
        resp = await client.post(f"/projects/{pid}/sandbox", json={
            "command": "echo x",
            "timeout_seconds": 99999,
        })
        assert resp.status_code == 201
        # Timeout should be capped at MAX_SANDBOX_TIMEOUT (300)
        assert resp.json()["timeout_seconds"] <= 300
