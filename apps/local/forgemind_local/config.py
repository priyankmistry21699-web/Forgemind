"""ForgeMind Local configuration model.

Manages the `.forgemind/config.yaml` file that lives in a repository root.
"""

from __future__ import annotations

import os
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

CONFIG_DIR = ".forgemind"
CONFIG_FILE = "config.yaml"
STATE_DIR = "state"
CACHE_DIR = "cache"
INDEX_DIR = "index"
PATCHES_DIR = "patches"
SNAPSHOTS_DIR = "snapshots"

EXECUTION_POLICY_SAFE = "safe"
EXECUTION_POLICY_PERMISSIVE = "permissive"
EXECUTION_POLICY_LOCKED = "locked"


@dataclass
class LocalConfig:
    """Local ForgeMind workspace configuration."""

    workspace_id: str = ""
    workspace_slug: str = ""
    project_id: str = ""
    project_slug: str = ""
    repo_root: str = ""
    local_storage_path: str = ""
    cache_path: str = ""
    mode: str = "hybrid"  # offline | hybrid | remote
    sync_enabled: bool = False
    execution_policy: str = EXECUTION_POLICY_SAFE
    editor_integration: bool = True
    created_at: str = ""

    # Derived / internal
    _config_dir: str = field(default="", repr=False)

    @classmethod
    def default(cls, repo_root: str) -> "LocalConfig":
        """Create a default config for a new init."""
        config_dir = os.path.join(repo_root, CONFIG_DIR)
        return cls(
            workspace_id=str(uuid.uuid4()),
            workspace_slug=Path(repo_root).name.lower().replace(" ", "-"),
            project_id=str(uuid.uuid4()),
            project_slug=Path(repo_root).name.lower().replace(" ", "-"),
            repo_root=repo_root,
            local_storage_path=os.path.join(config_dir, STATE_DIR),
            cache_path=os.path.join(config_dir, CACHE_DIR),
            mode="hybrid",
            sync_enabled=False,
            execution_policy=EXECUTION_POLICY_SAFE,
            editor_integration=True,
            created_at="",
            _config_dir=config_dir,
        )

    # ── Serialisation ──────────────────────────────────────────────

    def to_dict(self) -> dict[str, Any]:
        return {
            "workspace_id": self.workspace_id,
            "workspace_slug": self.workspace_slug,
            "project_id": self.project_id,
            "project_slug": self.project_slug,
            "repo_root": self.repo_root,
            "local_storage_path": self.local_storage_path,
            "cache_path": self.cache_path,
            "mode": self.mode,
            "sync_enabled": self.sync_enabled,
            "execution_policy": self.execution_policy,
            "editor_integration": self.editor_integration,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any], config_dir: str = "") -> "LocalConfig":
        return cls(
            workspace_id=data.get("workspace_id", ""),
            workspace_slug=data.get("workspace_slug", ""),
            project_id=data.get("project_id", ""),
            project_slug=data.get("project_slug", ""),
            repo_root=data.get("repo_root", ""),
            local_storage_path=data.get("local_storage_path", ""),
            cache_path=data.get("cache_path", ""),
            mode=data.get("mode", "hybrid"),
            sync_enabled=data.get("sync_enabled", False),
            execution_policy=data.get("execution_policy", EXECUTION_POLICY_SAFE),
            editor_integration=data.get("editor_integration", True),
            created_at=data.get("created_at", ""),
            _config_dir=config_dir,
        )


# ── File I/O ──────────────────────────────────────────────────────


def config_dir_for(repo_root: str) -> str:
    return os.path.join(repo_root, CONFIG_DIR)


def config_path_for(repo_root: str) -> str:
    return os.path.join(repo_root, CONFIG_DIR, CONFIG_FILE)


def load_config(repo_root: str) -> LocalConfig | None:
    """Load config from `.forgemind/config.yaml`. Returns None if missing."""
    path = config_path_for(repo_root)
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    return LocalConfig.from_dict(data, config_dir=config_dir_for(repo_root))


def save_config(cfg: LocalConfig) -> str:
    """Persist config to disk. Returns the config file path."""
    cfg_dir = config_dir_for(cfg.repo_root)
    os.makedirs(cfg_dir, exist_ok=True)
    path = config_path_for(cfg.repo_root)
    with open(path, "w", encoding="utf-8") as fh:
        yaml.dump(cfg.to_dict(), fh, default_flow_style=False, sort_keys=False)
    return path


def ensure_directories(cfg: LocalConfig) -> list[str]:
    """Create all required local directories. Returns list of dirs created."""
    created: list[str] = []
    for d in [
        config_dir_for(cfg.repo_root),
        cfg.local_storage_path,
        cfg.cache_path,
        os.path.join(config_dir_for(cfg.repo_root), INDEX_DIR),
        os.path.join(config_dir_for(cfg.repo_root), PATCHES_DIR),
        os.path.join(config_dir_for(cfg.repo_root), SNAPSHOTS_DIR),
    ]:
        if d and not os.path.isdir(d):
            os.makedirs(d, exist_ok=True)
            created.append(d)
    return created


def detect_repo_root(start: str | None = None) -> str | None:
    """Walk up from *start* (default cwd) looking for a .git directory."""
    current = Path(start or os.getcwd()).resolve()
    for p in [current, *current.parents]:
        if (p / ".git").is_dir():
            return str(p)
    return None
