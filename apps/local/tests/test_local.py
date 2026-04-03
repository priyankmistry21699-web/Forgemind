"""FM-100 — Tests for ForgeMind Local (FM-091 → FM-099).

Covers configuration, repo indexing, local chat, execution sandbox,
patch workflow, PR preparation, IDE integration, state management,
and handoff snapshots.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

# ── Fixtures ───────────────────────────────────────────────────────


@pytest.fixture()
def repo(tmp_path: Path) -> Path:
    """Create a minimal fake repo with .git/ and a few source files."""
    (tmp_path / ".git").mkdir()
    (tmp_path / "main.py").write_text("print('hello')\n", encoding="utf-8")
    (tmp_path / "utils.py").write_text(
        "def add(a, b):\n    return a + b\n\ndef greet(name):\n    return f'hi {name}'\n",
        encoding="utf-8",
    )
    (tmp_path / "pyproject.toml").write_text(
        "[project]\nname='demo'\n", encoding="utf-8"
    )
    sub = tmp_path / "pkg"
    sub.mkdir()
    (sub / "__init__.py").write_text("", encoding="utf-8")
    (sub / "app.py").write_text("# entrypoint\n", encoding="utf-8")
    return tmp_path


@pytest.fixture()
def inited_repo(repo: Path) -> Path:
    """A repo that has already been initialised with ``forgemind init``."""
    from forgemind_local.config import LocalConfig, ensure_directories, save_config

    cfg = LocalConfig.default(str(repo))
    save_config(cfg)
    ensure_directories(cfg)
    return repo


# ======================================================================
# FM-091  Local Foundation — Config & Directory Management
# ======================================================================


class TestConfig:
    def test_default_config_fields(self, repo: Path) -> None:
        from forgemind_local.config import LocalConfig

        cfg = LocalConfig.default(str(repo))
        assert cfg.workspace_id
        assert cfg.workspace_slug == repo.name.lower().replace(" ", "-")
        assert cfg.mode == "hybrid"
        assert cfg.execution_policy == "safe"

    def test_save_and_load_roundtrip(self, repo: Path) -> None:
        from forgemind_local.config import LocalConfig, load_config, save_config

        cfg = LocalConfig.default(str(repo))
        cfg.mode = "offline"
        save_config(cfg)

        loaded = load_config(str(repo))
        assert loaded is not None
        assert loaded.mode == "offline"
        assert loaded.workspace_id == cfg.workspace_id

    def test_load_missing_returns_none(self, repo: Path) -> None:
        from forgemind_local.config import load_config

        assert load_config(str(repo)) is None

    def test_ensure_directories(self, repo: Path) -> None:
        from forgemind_local.config import LocalConfig, ensure_directories, save_config

        cfg = LocalConfig.default(str(repo))
        save_config(cfg)
        created = ensure_directories(cfg)
        assert len(created) > 0
        assert (repo / ".forgemind" / "state").is_dir()
        assert (repo / ".forgemind" / "cache").is_dir()
        assert (repo / ".forgemind" / "index").is_dir()
        assert (repo / ".forgemind" / "patches").is_dir()
        assert (repo / ".forgemind" / "snapshots").is_dir()

    def test_detect_repo_root(self, repo: Path) -> None:
        from forgemind_local.config import detect_repo_root

        root = detect_repo_root(str(repo / "pkg"))
        assert root == str(repo.resolve())

    def test_detect_repo_root_none(self, tmp_path: Path) -> None:
        from forgemind_local.config import detect_repo_root

        assert detect_repo_root(str(tmp_path)) is None

    def test_to_dict_and_from_dict(self, repo: Path) -> None:
        from forgemind_local.config import LocalConfig

        cfg = LocalConfig.default(str(repo))
        d = cfg.to_dict()
        restored = LocalConfig.from_dict(d)
        assert restored.workspace_id == cfg.workspace_id
        assert restored.mode == cfg.mode


# ======================================================================
# FM-092  Repo Attach & Indexing
# ======================================================================


class TestRepoIndex:
    def test_build_index(self, repo: Path) -> None:
        from forgemind_local.repo_index import build_repo_index

        manifest = build_repo_index(str(repo))
        assert manifest["total_files"] > 0
        assert manifest["total_lines"] > 0
        assert "Python" in manifest["language_breakdown"]
        paths = [f["path"] for f in manifest["files"]]
        assert "main.py" in paths

    def test_entrypoints_detected(self, repo: Path) -> None:
        from forgemind_local.repo_index import build_repo_index

        manifest = build_repo_index(str(repo))
        assert "main.py" in manifest["entrypoints"]
        assert "pkg/app.py" in manifest["entrypoints"]

    def test_build_files_detected(self, repo: Path) -> None:
        from forgemind_local.repo_index import build_repo_index

        manifest = build_repo_index(str(repo))
        assert "pyproject.toml" in manifest["build_files"]

    def test_ignore_dirs_skipped(self, repo: Path) -> None:
        from forgemind_local.repo_index import build_repo_index

        (repo / "node_modules").mkdir()
        (repo / "node_modules" / "junk.js").write_text("//\n", encoding="utf-8")
        manifest = build_repo_index(str(repo))
        paths = [f["path"] for f in manifest["files"]]
        assert not any("node_modules" in p for p in paths)

    def test_load_manifest_missing(self, repo: Path) -> None:
        from forgemind_local.repo_index import load_manifest

        assert load_manifest(str(repo)) is None

    def test_load_manifest_present(self, inited_repo: Path) -> None:
        from forgemind_local.repo_index import build_repo_index, load_manifest

        manifest = build_repo_index(str(inited_repo))
        idx_dir = inited_repo / ".forgemind" / "index"
        idx_dir.mkdir(parents=True, exist_ok=True)
        (idx_dir / "repo_manifest.json").write_text(
            json.dumps(manifest), encoding="utf-8"
        )
        loaded = load_manifest(str(inited_repo))
        assert loaded is not None
        assert loaded["total_files"] == manifest["total_files"]


# ======================================================================
# FM-093  Local Chat Over Codebase
# ======================================================================


class TestLocalChat:
    def test_answer_question_returns_dict(self, inited_repo: Path) -> None:
        from forgemind_local.local_chat import answer_question

        # Must index first
        self._build_and_save_manifest(inited_repo)
        result = answer_question(str(inited_repo), "where is the main entrypoint?")
        assert isinstance(result, dict)
        assert "answer" in result
        assert "citations" in result
        assert len(result["answer"]) > 0

    def test_answer_without_index_falls_back(self, inited_repo: Path) -> None:
        from forgemind_local.local_chat import answer_question

        result = answer_question(str(inited_repo), "hello")
        assert isinstance(result, dict)
        assert "answer" in result

    @staticmethod
    def _build_and_save_manifest(repo: Path) -> None:
        from forgemind_local.repo_index import build_repo_index

        manifest = build_repo_index(str(repo))
        idx_dir = repo / ".forgemind" / "index"
        idx_dir.mkdir(parents=True, exist_ok=True)
        (idx_dir / "repo_manifest.json").write_text(
            json.dumps(manifest), encoding="utf-8"
        )


# ======================================================================
# FM-094  Local Execution Sandbox
# ======================================================================


class TestLocalExec:
    def test_blocked_command(self, inited_repo: Path) -> None:
        from forgemind_local.local_exec import run_local_command

        result = run_local_command(str(inited_repo), "rm -rf /")
        assert result["blocked"] is True
        assert "blocked pattern" in result["reason"].lower()

    def test_safe_command_allowed(self, inited_repo: Path) -> None:
        from forgemind_local.local_exec import run_local_command

        result = run_local_command(str(inited_repo), "git status", policy="safe")
        assert result["blocked"] is False

    def test_unsafe_command_blocked_under_safe(self, inited_repo: Path) -> None:
        from forgemind_local.local_exec import run_local_command

        result = run_local_command(
            str(inited_repo), "curl http://example.com", policy="safe"
        )
        assert result["blocked"] is True

    def test_permissive_allows_more(self, inited_repo: Path) -> None:
        from forgemind_local.local_exec import run_local_command

        # echo should work under permissive
        result = run_local_command(str(inited_repo), "echo hello", policy="permissive")
        assert result["blocked"] is False
        assert result["returncode"] == 0

    def test_locked_blocks_everything(self, inited_repo: Path) -> None:
        from forgemind_local.local_exec import run_local_command

        result = run_local_command(str(inited_repo), "echo hi", policy="locked")
        assert result["blocked"] is True
        assert "locked" in result["reason"].lower()

    def test_run_logging(self, inited_repo: Path) -> None:
        from forgemind_local.local_exec import list_runs, run_local_command

        run_local_command(str(inited_repo), "git status", policy="safe")
        runs = list_runs(str(inited_repo))
        assert len(runs) >= 1
        assert runs[0]["command"] == "git status"

    def test_fork_bomb_blocked(self, inited_repo: Path) -> None:
        from forgemind_local.local_exec import run_local_command

        result = run_local_command(str(inited_repo), ":(){:|:&};:")
        assert result["blocked"] is True


# ======================================================================
# FM-095  Local Patch Workflow
# ======================================================================


class TestLocalPatch:
    def test_generate_and_list(self, inited_repo: Path) -> None:
        from forgemind_local.local_patch import generate_patch, list_patches

        # Create a change
        self._make_change(inited_repo)
        patch_info = generate_patch(str(inited_repo), "test fix")
        assert "patch_id" in patch_info
        assert "patch_path" in patch_info
        assert os.path.isfile(patch_info["patch_path"])

        patches = list_patches(str(inited_repo))
        assert len(patches) >= 1

    def test_preview_patch(self, inited_repo: Path) -> None:
        from forgemind_local.local_patch import generate_patch, preview_patch

        self._make_change(inited_repo)
        info = generate_patch(str(inited_repo), "preview test")
        content = preview_patch(str(inited_repo), info["patch_id"])
        assert isinstance(content, str)

    def test_apply_and_reject(self, inited_repo: Path) -> None:
        from forgemind_local.local_patch import (
            generate_patch,
            list_patches,
            reject_patch,
        )

        self._make_change(inited_repo)
        info = generate_patch(str(inited_repo), "reject test")
        reject_patch(str(inited_repo), info["patch_id"])

        # Should still appear in list but rejected
        patches = list_patches(str(inited_repo))
        rejected = [p for p in patches if p.get("status") == "rejected"]
        assert len(rejected) >= 1

    @staticmethod
    def _make_change(repo: Path) -> None:
        """Stage an uncommitted diff via git so generate_patch can read it."""
        import subprocess

        subprocess.run(["git", "init"], cwd=str(repo), capture_output=True, check=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=str(repo),
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "test"],
            cwd=str(repo),
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["git", "add", "."], cwd=str(repo), capture_output=True, check=True
        )
        subprocess.run(
            ["git", "commit", "-m", "init"],
            cwd=str(repo),
            capture_output=True,
            check=True,
        )
        # Now make a local change
        (repo / "utils.py").write_text(
            "def add(a, b):\n    return a + b + 0\n", encoding="utf-8"
        )


# ======================================================================
# FM-096  Local PR Preparation
# ======================================================================


class TestLocalPR:
    def test_prepare_pr(self, inited_repo: Path) -> None:
        from forgemind_local.local_pr import prepare_pr

        self._setup_git_with_branch(inited_repo)
        pr = prepare_pr(str(inited_repo))
        assert isinstance(pr, dict)
        assert "markdown" in pr
        assert "## " in pr["markdown"]  # has markdown headings
        assert "title" in pr
        assert "branch" in pr

    @staticmethod
    def _setup_git_with_branch(repo: Path) -> None:
        import subprocess

        subprocess.run(["git", "init"], cwd=str(repo), capture_output=True, check=True)
        subprocess.run(
            ["git", "config", "user.email", "t@t.com"],
            cwd=str(repo),
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "t"],
            cwd=str(repo),
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["git", "add", "."], cwd=str(repo), capture_output=True, check=True
        )
        subprocess.run(
            ["git", "commit", "-m", "initial"],
            cwd=str(repo),
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["git", "checkout", "-b", "feature/test"],
            cwd=str(repo),
            capture_output=True,
            check=True,
        )
        (repo / "new_file.py").write_text("# new\n", encoding="utf-8")
        subprocess.run(
            ["git", "add", "."], cwd=str(repo), capture_output=True, check=True
        )
        subprocess.run(
            ["git", "commit", "-m", "add feature"],
            cwd=str(repo),
            capture_output=True,
            check=True,
        )


# ======================================================================
# FM-097  IDE/Editor Integration
# ======================================================================


class TestIDEIntegration:
    def test_setup_editor_creates_tasks(self, inited_repo: Path) -> None:
        from forgemind_local.ide_integration import setup_editor

        created = setup_editor(str(inited_repo))
        assert len(created) > 0
        tasks_path = inited_repo / ".vscode" / "tasks.json"
        assert tasks_path.is_file()

        with open(tasks_path, encoding="utf-8") as fh:
            data = json.load(fh)
        labels = [t["label"] for t in data.get("tasks", [])]
        assert "ForgeMind: Status" in labels

    def test_setup_editor_idempotent(self, inited_repo: Path) -> None:
        from forgemind_local.ide_integration import setup_editor

        setup_editor(str(inited_repo))
        setup_editor(str(inited_repo))
        tasks_path = inited_repo / ".vscode" / "tasks.json"
        with open(tasks_path, encoding="utf-8") as fh:
            data = json.load(fh)
        # No duplicate tasks
        labels = [t["label"] for t in data.get("tasks", [])]
        assert len(labels) == len(set(labels))


# ======================================================================
# FM-098  Offline / Resilient State
# ======================================================================


class TestLocalState:
    def test_cache_put_and_get(self, inited_repo: Path) -> None:
        from forgemind_local.local_state import cache_get, cache_put

        cache_put(str(inited_repo), "test_key", {"a": 1}, ttl_s=3600)
        val = cache_get(str(inited_repo), "test_key")
        assert val == {"a": 1}

    def test_cache_expired(self, inited_repo: Path) -> None:
        from forgemind_local.local_state import cache_get, cache_put

        cache_put(str(inited_repo), "exp_key", "x", ttl_s=0)
        # TTL=0 means it expires instantly
        val = cache_get(str(inited_repo), "exp_key")
        assert val is None

    def test_cache_clear(self, inited_repo: Path) -> None:
        from forgemind_local.local_state import cache_clear, cache_put

        cache_put(str(inited_repo), "k1", 1)
        cache_put(str(inited_repo), "k2", 2)
        removed = cache_clear(str(inited_repo))
        assert removed == 2

    def test_queue_and_list(self, inited_repo: Path) -> None:
        from forgemind_local.local_state import list_queue, queue_event

        eid = queue_event(str(inited_repo), "test.event", {"a": 1})
        assert eid
        items = list_queue(str(inited_repo))
        assert len(items) >= 1
        assert items[0]["event_type"] == "test.event"

    def test_mark_synced_and_clear(self, inited_repo: Path) -> None:
        from forgemind_local.local_state import (
            clear_synced,
            list_queue,
            mark_synced,
            queue_event,
        )

        eid = queue_event(str(inited_repo), "sync.test", {})
        mark_synced(str(inited_repo), eid)

        # list_queue only shows unsynced
        pending = list_queue(str(inited_repo))
        assert all(i["event_id"] != eid for i in pending)

        removed = clear_synced(str(inited_repo))
        assert removed >= 1

    def test_mode_get_default(self, inited_repo: Path) -> None:
        from forgemind_local.local_state import get_mode

        assert get_mode(str(inited_repo)) in ("offline", "hybrid", "remote")

    def test_mode_set_and_get(self, inited_repo: Path) -> None:
        from forgemind_local.local_state import get_mode, set_mode

        set_mode(str(inited_repo), "offline")
        assert get_mode(str(inited_repo)) == "offline"

    def test_mode_invalid_raises(self, inited_repo: Path) -> None:
        from forgemind_local.local_state import set_mode

        with pytest.raises(ValueError):
            set_mode(str(inited_repo), "invalid")


# ======================================================================
# FM-099  Local Handoff / Snapshot
# ======================================================================


class TestLocalHandoff:
    def test_export_creates_zip(self, inited_repo: Path) -> None:
        from forgemind_local.local_handoff import export_snapshot

        path = export_snapshot(str(inited_repo))
        assert path.endswith(".zip")
        assert os.path.isfile(path)

    def test_export_import_roundtrip(self, inited_repo: Path, tmp_path: Path) -> None:
        from forgemind_local.local_handoff import export_snapshot, import_snapshot

        # Export from inited_repo
        zip_path = export_snapshot(str(inited_repo))

        # Import into a fresh repo
        target = tmp_path / "target"
        target.mkdir()
        (target / ".git").mkdir()
        manifest = import_snapshot(zip_path, str(target))

        assert "bundle_id" in manifest
        assert "exported_at" in manifest
        # Config should have been copied
        assert (target / ".forgemind" / "config.yaml").is_file()

    def test_inspect_bundle(self, inited_repo: Path) -> None:
        from forgemind_local.local_handoff import export_snapshot, inspect_bundle

        zip_path = export_snapshot(str(inited_repo))
        m = inspect_bundle(zip_path)
        assert "bundle_id" in m
        assert "contents" in m

    def test_import_missing_raises(self, inited_repo: Path) -> None:
        from forgemind_local.local_handoff import import_snapshot

        with pytest.raises(FileNotFoundError):
            import_snapshot("/nonexistent.zip", str(inited_repo))

    def test_import_does_not_overwrite_existing_config(
        self, inited_repo: Path, tmp_path: Path
    ) -> None:
        from forgemind_local.config import load_config, save_config, LocalConfig
        from forgemind_local.local_handoff import export_snapshot, import_snapshot

        zip_path = export_snapshot(str(inited_repo))

        # Target already has a config
        target = tmp_path / "target2"
        target.mkdir()
        (target / ".git").mkdir()
        fm_dir = target / ".forgemind"
        fm_dir.mkdir()
        cfg = LocalConfig.default(str(target))
        cfg.mode = "remote"
        save_config(cfg)

        import_snapshot(zip_path, str(target))
        # Mode should still be "remote", not overwritten
        loaded = load_config(str(target))
        assert loaded is not None
        assert loaded.mode == "remote"
