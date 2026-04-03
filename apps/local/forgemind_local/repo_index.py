"""FM-092 — Local repo attach and indexing.

Scans a repository, classifies files, builds a lightweight manifest with
language breakdown, entrypoints, build files, and per-file metadata.
"""

from __future__ import annotations

import datetime as _dt
import os
from pathlib import Path
from typing import Any

# ── Language detection by extension ────────────────────────────────

_EXT_MAP: dict[str, str] = {
    ".py": "Python",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript (JSX)",
    ".jsx": "JavaScript (JSX)",
    ".java": "Java",
    ".go": "Go",
    ".rs": "Rust",
    ".rb": "Ruby",
    ".c": "C",
    ".cpp": "C++",
    ".h": "C/C++ Header",
    ".cs": "C#",
    ".swift": "Swift",
    ".kt": "Kotlin",
    ".sql": "SQL",
    ".sh": "Shell",
    ".bash": "Shell",
    ".yml": "YAML",
    ".yaml": "YAML",
    ".json": "JSON",
    ".toml": "TOML",
    ".md": "Markdown",
    ".html": "HTML",
    ".css": "CSS",
    ".scss": "SCSS",
    ".dockerfile": "Docker",
    ".tf": "Terraform",
}

_IGNORE_DIRS = {
    ".git",
    ".forgemind",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    ".tox",
    ".mypy_cache",
    ".ruff_cache",
    ".pytest_cache",
    "dist",
    "build",
    ".next",
    "out",
    "coverage",
    ".eggs",
    "*.egg-info",
}

_BUILD_FILES = {
    "pyproject.toml",
    "setup.py",
    "setup.cfg",
    "package.json",
    "Cargo.toml",
    "go.mod",
    "Gemfile",
    "Makefile",
    "CMakeLists.txt",
    "docker-compose.yml",
    "docker-compose.yaml",
    "Dockerfile",
    "Jenkinsfile",
    ".github/workflows",
}

_ENTRYPOINT_PATTERNS = {
    "main.py",
    "app.py",
    "server.py",
    "cli.py",
    "manage.py",
    "index.ts",
    "index.js",
    "main.ts",
    "main.go",
    "main.rs",
}


def _should_ignore(name: str) -> bool:
    return name in _IGNORE_DIRS or name.endswith(".egg-info")


def _count_lines(path: str) -> int:
    try:
        with open(path, encoding="utf-8", errors="ignore") as fh:
            return sum(1 for _ in fh)
    except Exception:
        return 0


def _detect_language(ext: str, filename: str) -> str:
    if filename.lower() == "dockerfile":
        return "Docker"
    return _EXT_MAP.get(ext.lower(), "Other")


# ── Main index builder ─────────────────────────────────────────────


def build_repo_index(repo_root: str) -> dict[str, Any]:
    """Walk *repo_root* and produce a structured manifest."""
    root = Path(repo_root).resolve()
    files: list[dict[str, Any]] = []
    lang_stats: dict[str, dict[str, int]] = {}
    build_files_found: list[str] = []
    entrypoints_found: list[str] = []
    total_lines = 0

    for dirpath, dirnames, filenames in os.walk(root):
        # Prune ignored dirs in-place
        dirnames[:] = [d for d in dirnames if not _should_ignore(d)]

        rel_dir = os.path.relpath(dirpath, root)
        if rel_dir == ".":
            rel_dir = ""

        for fname in filenames:
            rel = os.path.join(rel_dir, fname) if rel_dir else fname
            full = os.path.join(dirpath, fname)
            ext = os.path.splitext(fname)[1]
            lang = _detect_language(ext, fname)
            lines = _count_lines(full)
            total_lines += lines

            entry: dict[str, Any] = {
                "path": rel.replace("\\", "/"),
                "language": lang,
                "lines": lines,
                "extension": ext,
            }
            files.append(entry)

            # Language stats
            bucket = lang_stats.setdefault(lang, {"files": 0, "lines": 0})
            bucket["files"] += 1
            bucket["lines"] += lines

            # Build files
            if fname in _BUILD_FILES:
                build_files_found.append(rel.replace("\\", "/"))

            # Entrypoints
            if fname in _ENTRYPOINT_PATTERNS:
                entrypoints_found.append(rel.replace("\\", "/"))

    manifest: dict[str, Any] = {
        "repo_root": str(root),
        "scanned_at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "total_files": len(files),
        "total_lines": total_lines,
        "language_breakdown": lang_stats,
        "build_files": build_files_found,
        "entrypoints": entrypoints_found,
        "files": files,
    }
    return manifest


def load_manifest(repo_root: str) -> dict[str, Any] | None:
    """Load an existing manifest from the index directory."""
    import json

    path = os.path.join(repo_root, ".forgemind", "index", "repo_manifest.json")
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)
