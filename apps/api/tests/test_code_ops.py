"""Tests for code operations endpoints (FM-061 through FM-069)."""
import uuid
import pytest
from httpx import AsyncClient

STUB_USER_ID = "00000000-0000-0000-0000-000000000001"


@pytest.mark.asyncio
class TestCodeMappings:

    async def test_create_mapping(self, client: AsyncClient, sample_project, sample_artifact):
        pid = str(sample_project.id)
        aid = str(sample_artifact.id)
        resp = await client.post(f"/projects/{pid}/code-mappings", json={
            "artifact_id": aid, "file_path": "src/main.py", "language": "python",
        })
        assert resp.status_code == 201
        assert resp.json()["file_path"] == "src/main.py"

    async def test_list_mappings(self, client: AsyncClient, sample_project, sample_artifact):
        pid = str(sample_project.id)
        aid = str(sample_artifact.id)
        await client.post(f"/projects/{pid}/code-mappings", json={
            "artifact_id": aid, "file_path": "src/a.py",
        })
        resp = await client.get(f"/projects/{pid}/code-mappings")
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    async def test_delete_mapping(self, client: AsyncClient, sample_project, sample_artifact):
        pid = str(sample_project.id)
        aid = str(sample_artifact.id)
        create = await client.post(f"/projects/{pid}/code-mappings", json={
            "artifact_id": aid, "file_path": "src/del.py",
        })
        mid = create.json()["id"]
        resp = await client.delete(f"/code-mappings/{mid}")
        assert resp.status_code == 204


@pytest.mark.asyncio
class TestPatchProposals:

    async def test_create_patch(self, client: AsyncClient, sample_project):
        pid = str(sample_project.id)
        resp = await client.post(f"/projects/{pid}/patches", json={
            "title": "Fix bug",
            "diff_content": "--- a/x.py\n+++ b/x.py\n-old\n+new",
        })
        assert resp.status_code == 201
        assert resp.json()["status"] == "draft"

    async def test_list_patches(self, client: AsyncClient, sample_project):
        pid = str(sample_project.id)
        await client.post(f"/projects/{pid}/patches", json={
            "title": "P1", "diff_content": "diff",
        })
        resp = await client.get(f"/projects/{pid}/patches")
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    async def test_get_patch(self, client: AsyncClient, sample_project):
        pid = str(sample_project.id)
        create = await client.post(f"/projects/{pid}/patches", json={
            "title": "G", "diff_content": "d",
        })
        patch_id = create.json()["id"]
        resp = await client.get(f"/patches/{patch_id}")
        assert resp.status_code == 200

    async def test_update_patch(self, client: AsyncClient, sample_project):
        pid = str(sample_project.id)
        create = await client.post(f"/projects/{pid}/patches", json={
            "title": "U", "diff_content": "d",
        })
        patch_id = create.json()["id"]
        resp = await client.patch(f"/patches/{patch_id}", json={
            "status": "proposed",
        })
        assert resp.status_code == 200
        assert resp.json()["status"] == "proposed"


@pytest.mark.asyncio
class TestChangeReviews:

    async def test_create_review(self, client: AsyncClient, sample_project):
        pid = str(sample_project.id)
        patch = await client.post(f"/projects/{pid}/patches", json={
            "title": "Rev", "diff_content": "d",
        })
        patch_id = patch.json()["id"]
        resp = await client.post(f"/patches/{patch_id}/reviews", json={
            "decision": "approve", "comment": "LGTM",
        })
        assert resp.status_code == 201
        assert resp.json()["decision"] == "approve"

    async def test_list_reviews(self, client: AsyncClient, sample_project):
        pid = str(sample_project.id)
        patch = await client.post(f"/projects/{pid}/patches", json={
            "title": "LR", "diff_content": "d",
        })
        patch_id = patch.json()["id"]
        await client.post(f"/patches/{patch_id}/reviews", json={
            "decision": "comment",
        })
        resp = await client.get(f"/patches/{patch_id}/reviews")
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1


@pytest.mark.asyncio
class TestBranchStrategies:

    async def test_create_strategy(self, client: AsyncClient, sample_project):
        pid = str(sample_project.id)
        resp = await client.post(f"/projects/{pid}/branch-strategies", json={})
        assert resp.status_code == 201
        assert resp.json()["base_branch"] == "main"

    async def test_list_strategies(self, client: AsyncClient, sample_project):
        pid = str(sample_project.id)
        await client.post(f"/projects/{pid}/branch-strategies", json={})
        resp = await client.get(f"/projects/{pid}/branch-strategies")
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    async def test_update_strategy(self, client: AsyncClient, sample_project):
        pid = str(sample_project.id)
        create = await client.post(f"/projects/{pid}/branch-strategies", json={})
        sid = create.json()["id"]
        resp = await client.patch(f"/branch-strategies/{sid}", json={
            "base_branch": "develop",
        })
        assert resp.status_code == 200
        assert resp.json()["base_branch"] == "develop"


@pytest.mark.asyncio
class TestPRDrafts:

    async def test_create_pr_draft(self, client: AsyncClient, sample_project):
        pid = str(sample_project.id)
        resp = await client.post(f"/projects/{pid}/pr-drafts", json={
            "title": "Add feature X",
            "source_branch": "feature/x",
        })
        assert resp.status_code == 201
        assert resp.json()["status"] == "draft"

    async def test_list_pr_drafts(self, client: AsyncClient, sample_project):
        pid = str(sample_project.id)
        await client.post(f"/projects/{pid}/pr-drafts", json={
            "title": "PR1", "source_branch": "f/1",
        })
        resp = await client.get(f"/projects/{pid}/pr-drafts")
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    async def test_get_pr_draft(self, client: AsyncClient, sample_project):
        pid = str(sample_project.id)
        create = await client.post(f"/projects/{pid}/pr-drafts", json={
            "title": "GP", "source_branch": "gp/1",
        })
        pr_id = create.json()["id"]
        resp = await client.get(f"/pr-drafts/{pr_id}")
        assert resp.status_code == 200

    async def test_update_pr_draft(self, client: AsyncClient, sample_project):
        pid = str(sample_project.id)
        create = await client.post(f"/projects/{pid}/pr-drafts", json={
            "title": "UP", "source_branch": "u/1",
        })
        pr_id = create.json()["id"]
        resp = await client.patch(f"/pr-drafts/{pr_id}", json={
            "status": "ready",
        })
        assert resp.status_code == 200
        assert resp.json()["status"] == "ready"


@pytest.mark.asyncio
class TestRepoActionApprovals:

    async def test_create_approval(self, client: AsyncClient, sample_project):
        pid = str(sample_project.id)
        resp = await client.post(f"/projects/{pid}/repo-approvals", json={
            "action_type": "push", "reason": "Deploy fix",
        })
        assert resp.status_code == 201
        assert resp.json()["status"] == "pending"

    async def test_decide_approval(self, client: AsyncClient, sample_project):
        pid = str(sample_project.id)
        create = await client.post(f"/projects/{pid}/repo-approvals", json={
            "action_type": "merge",
        })
        aid = create.json()["id"]
        resp = await client.post(f"/repo-approvals/{aid}/decide", json={
            "status": "approved", "decision_comment": "OK",
        })
        assert resp.status_code == 200
        assert resp.json()["status"] == "approved"

    async def test_list_approvals(self, client: AsyncClient, sample_project):
        pid = str(sample_project.id)
        await client.post(f"/projects/{pid}/repo-approvals", json={
            "action_type": "pr_create",
        })
        resp = await client.get(f"/projects/{pid}/repo-approvals")
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1


@pytest.mark.asyncio
class TestSandboxExecutions:

    async def test_create_execution(self, client: AsyncClient, sample_project):
        pid = str(sample_project.id)
        resp = await client.post(f"/projects/{pid}/sandbox", json={
            "command": "echo hello",
        })
        assert resp.status_code == 201
        assert resp.json()["status"] == "queued"

    async def test_list_executions(self, client: AsyncClient, sample_project):
        pid = str(sample_project.id)
        await client.post(f"/projects/{pid}/sandbox", json={
            "command": "ls",
        })
        resp = await client.get(f"/projects/{pid}/sandbox")
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    async def test_get_execution(self, client: AsyncClient, sample_project):
        pid = str(sample_project.id)
        create = await client.post(f"/projects/{pid}/sandbox", json={
            "command": "pwd",
        })
        eid = create.json()["id"]
        resp = await client.get(f"/sandbox/{eid}")
        assert resp.status_code == 200

    async def test_get_execution_404(self, client: AsyncClient):
        resp = await client.get(f"/sandbox/{uuid.uuid4()}")
        assert resp.status_code == 404
