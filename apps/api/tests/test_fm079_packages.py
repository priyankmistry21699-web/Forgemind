"""Tests for FM-079 — Monorepo package extraction.

Validates that all 4 extracted packages have real, importable code.
"""

import pathlib
import json

# Workspace root: tests/ -> api/ -> apps/ -> Forgemind/
_ROOT = pathlib.Path(__file__).resolve().parents[3]


# ── Package presence ─────────────────────────────────────────────


def test_schemas_package_has_source():
    """packages/schemas has real TypeScript source files."""
    schemas_src = _ROOT / "packages" / "schemas" / "src"
    assert schemas_src.exists(), "packages/schemas/src/ directory missing"
    ts_files = list(schemas_src.glob("*.ts"))
    # 22 domain modules + 1 barrel index.ts
    assert len(ts_files) >= 23, f"Expected ≥23 .ts files, got {len(ts_files)}"


def test_schemas_barrel_export():
    """packages/schemas/src/index.ts re-exports all domain modules."""
    index_ts = _ROOT / "packages" / "schemas" / "src" / "index.ts"
    content = index_ts.read_text()
    for module in [
        "activity",
        "agent",
        "approval",
        "artifact",
        "audit",
        "connector",
        "cost",
        "council",
        "escalation",
        "execution-event",
        "governance",
        "knowledge",
        "notification",
        "planner",
        "project-member",
        "project",
        "replay",
        "run",
        "task",
        "trust",
        "vault",
        "workspace",
    ]:
        assert f'from "./{module}"' in content, f"Missing re-export for {module}"


def test_schemas_package_json():
    """packages/schemas/package.json has correct metadata."""
    pkg_json = _ROOT / "packages" / "schemas" / "package.json"
    data = json.loads(pkg_json.read_text())
    assert data["name"] == "@forgemind/types"
    assert "src/index.ts" in data.get("main", "")


# ── Utils package ────────────────────────────────────────────────


def test_utils_package_structure():
    """packages/utils has pyproject.toml and forgemind_utils/ with modules."""
    base = _ROOT / "packages" / "utils"
    assert (base / "pyproject.toml").exists()
    pkg = base / "forgemind_utils"
    assert (pkg / "__init__.py").exists()
    assert (pkg / "metrics.py").exists()
    assert (pkg / "rate_limit.py").exists()
    assert (pkg / "error_handlers.py").exists()
    assert (pkg / "logging_middleware.py").exists()


def test_utils_metrics_module():
    """Utils metrics module has core functions."""
    from forgemind_utils.metrics import (
        inc_counter,
        get_counter,
        reset_metrics,
        render_prometheus,
    )

    reset_metrics()
    inc_counter("test_pkg_counter", 5.0)
    assert get_counter("test_pkg_counter") == 5.0
    output = render_prometheus()
    assert "test_pkg_counter" in output
    reset_metrics()


# ── Security package ─────────────────────────────────────────────


def test_security_package_structure():
    """packages/security has pyproject.toml and forgemind_security/ with modules."""
    base = _ROOT / "packages" / "security"
    assert (base / "pyproject.toml").exists()
    pkg = base / "forgemind_security"
    assert (pkg / "__init__.py").exists()
    assert (pkg / "jwt.py").exists()
    assert (pkg / "rbac.py").exists()


def test_security_rbac_engine():
    """RBAC permission matrices are importable and correct."""
    from forgemind_security.rbac import (
        Action,
        WorkspaceRole,
        ProjectRole,
        is_workspace_action_allowed,
        is_project_action_allowed,
    )

    assert is_workspace_action_allowed(WorkspaceRole.OWNER, Action.WORKSPACE_DELETE)
    assert not is_workspace_action_allowed(
        WorkspaceRole.VIEWER, Action.WORKSPACE_DELETE
    )
    assert is_project_action_allowed(ProjectRole.LEAD, Action.PROJECT_RUN)
    assert not is_project_action_allowed(ProjectRole.VIEWER, Action.PROJECT_RUN)


def test_security_jwt_helpers():
    """JWT create/decode round-trip works."""
    import uuid
    from forgemind_security.jwt import create_token, decode_token, JWTConfig

    cfg = JWTConfig(secret="test-secret-for-fm079")
    uid = uuid.uuid4()
    token = create_token(uid, cfg)
    payload = decode_token(token, cfg)
    assert payload["sub"] == str(uid)


# ── Core package ─────────────────────────────────────────────────


def test_core_package_structure():
    """packages/core has pyproject.toml and forgemind_core/ with modules."""
    base = _ROOT / "packages" / "core"
    assert (base / "pyproject.toml").exists()
    pkg = base / "forgemind_core"
    assert (pkg / "__init__.py").exists()
    assert (pkg / "constants.py").exists()
    assert (pkg / "llm.py").exists()


def test_core_constants():
    """Domain constant sets are populated and frozen."""
    from forgemind_core.constants import (
        PROJECT_STATUSES,
        RUN_STATUSES,
        TASK_STATUSES,
        ARTIFACT_TYPES,
        AGENT_STATUSES,
    )

    assert "active" in PROJECT_STATUSES
    assert "running" in RUN_STATUSES
    assert "completed" in TASK_STATUSES
    assert "implementation" in ARTIFACT_TYPES
    assert "deprecated" in AGENT_STATUSES

    # Ensure they are frozen (immutable)
    for s in [
        PROJECT_STATUSES,
        RUN_STATUSES,
        TASK_STATUSES,
        ARTIFACT_TYPES,
        AGENT_STATUSES,
    ]:
        assert isinstance(s, frozenset)
