"""FM-095 — Local patch workflow.

Generate, preview, apply, and reject unified-diff patches locally.
"""

from __future__ import annotations

import datetime as _dt
import json
import os
import subprocess
import uuid
from typing import Any


def _patches_dir(repo_root: str) -> str:
    return os.path.join(repo_root, ".forgemind", "patches")


def _meta_path(repo_root: str, patch_id: str) -> str:
    return os.path.join(_patches_dir(repo_root), f"{patch_id}.json")


def _diff_path(repo_root: str, patch_id: str) -> str:
    return os.path.join(_patches_dir(repo_root), f"{patch_id}.patch")


# ── Generate ───────────────────────────────────────────────────────


def generate_patch(
    repo_root: str,
    description: str,
    *,
    target_file: str | None = None,
) -> dict[str, Any]:
    """Generate a patch from the current working-tree diff.

    If *target_file* is given, only diff that file.
    The patch and metadata are persisted under `.forgemind/patches/`.
    """
    patch_id = str(uuid.uuid4())
    patches = _patches_dir(repo_root)
    os.makedirs(patches, exist_ok=True)

    # Produce diff
    cmd = ["git", "diff"]
    if target_file:
        cmd.append("--")
        cmd.append(target_file)

    proc = subprocess.run(
        cmd, cwd=repo_root, capture_output=True, text=True, timeout=30
    )
    diff_text = proc.stdout

    # If nothing in working tree, try staged
    if not diff_text.strip():
        cmd_staged = ["git", "diff", "--cached"]
        if target_file:
            cmd_staged += ["--", target_file]
        proc2 = subprocess.run(
            cmd_staged, cwd=repo_root, capture_output=True, text=True, timeout=30
        )
        diff_text = proc2.stdout

    # Write diff file
    diff_file = _diff_path(repo_root, patch_id)
    with open(diff_file, "w", encoding="utf-8") as fh:
        fh.write(diff_text)

    # Write metadata
    meta: dict[str, Any] = {
        "patch_id": patch_id,
        "description": description,
        "target_file": target_file,
        "status": "pending",
        "created_at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "lines_added": diff_text.count("\n+") if diff_text else 0,
        "lines_removed": diff_text.count("\n-") if diff_text else 0,
    }
    with open(_meta_path(repo_root, patch_id), "w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=2)

    return {"patch_id": patch_id, "patch_path": diff_file, "meta": meta}


# ── List ───────────────────────────────────────────────────────────


def list_patches(repo_root: str) -> list[dict[str, Any]]:
    """Return metadata for all patches."""
    patches = _patches_dir(repo_root)
    if not os.path.isdir(patches):
        return []
    result: list[dict[str, Any]] = []
    for fname in sorted(os.listdir(patches)):
        if fname.endswith(".json"):
            with open(os.path.join(patches, fname), encoding="utf-8") as fh:
                result.append(json.load(fh))
    return result


# ── Preview ────────────────────────────────────────────────────────


def preview_patch(repo_root: str, patch_id: str) -> str | None:
    """Return the diff text for a patch, or None if not found."""
    # Support prefix matching
    patch_id = _resolve_id(repo_root, patch_id)
    if patch_id is None:
        return None
    path = _diff_path(repo_root, patch_id)
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as fh:
        return fh.read()


# ── Apply ──────────────────────────────────────────────────────────


def apply_patch(repo_root: str, patch_id: str) -> bool:
    """Apply a patch to the working tree. Returns True on success."""
    patch_id = _resolve_id(repo_root, patch_id) or patch_id
    diff_file = _diff_path(repo_root, patch_id)
    if not os.path.isfile(diff_file):
        return False

    proc = subprocess.run(
        ["git", "apply", "--stat", "--check", diff_file],
        cwd=repo_root,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if proc.returncode != 0:
        return False

    proc2 = subprocess.run(
        ["git", "apply", diff_file],
        cwd=repo_root,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if proc2.returncode == 0:
        _update_status(repo_root, patch_id, "applied")
        return True
    return False


# ── Reject ─────────────────────────────────────────────────────────


def reject_patch(repo_root: str, patch_id: str) -> None:
    """Mark a patch as rejected."""
    patch_id = _resolve_id(repo_root, patch_id) or patch_id
    _update_status(repo_root, patch_id, "rejected")


# ── Helpers ────────────────────────────────────────────────────────


def _resolve_id(repo_root: str, prefix: str) -> str | None:
    """Resolve a short prefix to the full patch ID."""
    patches = _patches_dir(repo_root)
    if not os.path.isdir(patches):
        return None
    for fname in os.listdir(patches):
        if fname.startswith(prefix) and fname.endswith(".json"):
            return fname.removesuffix(".json")
    return None


def _update_status(repo_root: str, patch_id: str, status: str) -> None:
    meta_file = _meta_path(repo_root, patch_id)
    if not os.path.isfile(meta_file):
        return
    with open(meta_file, encoding="utf-8") as fh:
        meta = json.load(fh)
    meta["status"] = status
    meta["updated_at"] = _dt.datetime.now(_dt.timezone.utc).isoformat()
    with open(meta_file, "w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=2)
