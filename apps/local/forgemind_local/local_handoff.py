"""FM-099 — Local handoff / snapshot support.

Export and import local ForgeMind state bundles for continuity and
collaboration between developers or sessions.
"""

from __future__ import annotations

import datetime as _dt
import json
import os
import shutil
import tempfile
import uuid
from pathlib import Path
from typing import Any

from forgemind_local.config import load_config

# ── Export ──────────────────────────────────────────────────────────


def export_snapshot(repo_root: str, *, output_path: str | None = None) -> str:
    """Export a local handoff snapshot as a zip bundle.

    The bundle includes:
    - config.yaml
    - repo manifest (index)
    - patches (metadata only, no large diffs by default)
    - sync queue
    - recent run logs (last 20)
    - PR summaries
    - bundle manifest

    Returns the path to the created zip file.
    """
    cfg = load_config(repo_root)
    if cfg is None:
        raise RuntimeError("Not initialised. Run `forgemind init` first.")

    bundle_id = str(uuid.uuid4())[:8]
    timestamp = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    slug = cfg.workspace_slug or "forgemind"

    with tempfile.TemporaryDirectory() as staging:
        bundle_dir = os.path.join(staging, f"{slug}-{timestamp}")
        os.makedirs(bundle_dir)

        # 1. Config
        config_src = os.path.join(repo_root, ".forgemind", "config.yaml")
        if os.path.isfile(config_src):
            shutil.copy2(config_src, os.path.join(bundle_dir, "config.yaml"))

        # 2. Index / manifest
        manifest_src = os.path.join(
            repo_root, ".forgemind", "index", "repo_manifest.json"
        )
        if os.path.isfile(manifest_src):
            os.makedirs(os.path.join(bundle_dir, "index"), exist_ok=True)
            shutil.copy2(
                manifest_src, os.path.join(bundle_dir, "index", "repo_manifest.json")
            )

        # 3. Patches (metadata only for safety)
        patches_src = os.path.join(repo_root, ".forgemind", "patches")
        if os.path.isdir(patches_src):
            patches_dst = os.path.join(bundle_dir, "patches")
            os.makedirs(patches_dst, exist_ok=True)
            for f in os.listdir(patches_src):
                if f.endswith(".json"):
                    shutil.copy2(
                        os.path.join(patches_src, f), os.path.join(patches_dst, f)
                    )

        # 4. Sync queue
        queue_src = os.path.join(repo_root, ".forgemind", "state", "sync_queue")
        if os.path.isdir(queue_src):
            queue_dst = os.path.join(bundle_dir, "sync_queue")
            os.makedirs(queue_dst, exist_ok=True)
            for f in sorted(os.listdir(queue_src))[-50:]:  # last 50
                shutil.copy2(os.path.join(queue_src, f), os.path.join(queue_dst, f))

        # 5. Run logs (last 20)
        runs_src = os.path.join(repo_root, ".forgemind", "state", "runs")
        if os.path.isdir(runs_src):
            runs_dst = os.path.join(bundle_dir, "runs")
            os.makedirs(runs_dst, exist_ok=True)
            run_files = sorted(os.listdir(runs_src))[-20:]
            for f in run_files:
                shutil.copy2(os.path.join(runs_src, f), os.path.join(runs_dst, f))

        # 6. PR summary
        pr_src = os.path.join(repo_root, ".forgemind", "state", "pr_summary.md")
        if os.path.isfile(pr_src):
            shutil.copy2(pr_src, os.path.join(bundle_dir, "pr_summary.md"))

        # 6b. Checkpoints (FM-129)
        cp_src = os.path.join(repo_root, ".forgemind", "state", "checkpoints")
        if os.path.isdir(cp_src):
            cp_dst = os.path.join(bundle_dir, "checkpoints")
            shutil.copytree(cp_src, cp_dst)

        # 7. Bundle manifest
        bundle_manifest: dict[str, Any] = {
            "bundle_id": bundle_id,
            "exported_at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
            "workspace_slug": cfg.workspace_slug,
            "project_slug": cfg.project_slug,
            "repo_root": cfg.repo_root,
            "mode": cfg.mode,
            "template_slug": cfg.template_slug,
            "phase_profiles": cfg.phase_profiles,
            "contents": sorted(
                str(Path(p).relative_to(bundle_dir)).replace("\\", "/")
                for p in _walk_files(bundle_dir)
            ),
        }
        with open(
            os.path.join(bundle_dir, "manifest.json"), "w", encoding="utf-8"
        ) as fh:
            json.dump(bundle_manifest, fh, indent=2)

        # Zip it
        if output_path is None:
            snapshots_dir = os.path.join(repo_root, ".forgemind", "snapshots")
            os.makedirs(snapshots_dir, exist_ok=True)
            output_path = os.path.join(snapshots_dir, f"{slug}-{timestamp}")

        archive = shutil.make_archive(
            output_path, "zip", staging, os.path.basename(bundle_dir)
        )
        return archive


# ── Import ─────────────────────────────────────────────────────────


def import_snapshot(bundle_path: str, repo_root: str) -> dict[str, Any]:
    """Import a handoff snapshot bundle into the local .forgemind/ directory.

    Returns the bundle manifest.
    """
    if not os.path.isfile(bundle_path):
        raise FileNotFoundError(f"Bundle not found: {bundle_path}")

    with tempfile.TemporaryDirectory() as staging:
        shutil.unpack_archive(bundle_path, staging)

        # Find the manifest
        manifest = None
        manifest_path = None
        for root_dir, _, files in os.walk(staging):
            if "manifest.json" in files:
                manifest_path = os.path.join(root_dir, "manifest.json")
                with open(manifest_path, encoding="utf-8") as fh:
                    manifest = json.load(fh)
                break

        if manifest is None:
            raise ValueError("Invalid bundle: no manifest.json found")

        bundle_root = os.path.dirname(manifest_path)
        fm_dir = os.path.join(repo_root, ".forgemind")
        os.makedirs(fm_dir, exist_ok=True)

        # Copy config (don't overwrite if exists)
        src_config = os.path.join(bundle_root, "config.yaml")
        dst_config = os.path.join(fm_dir, "config.yaml")
        if os.path.isfile(src_config) and not os.path.isfile(dst_config):
            shutil.copy2(src_config, dst_config)

        # Copy index
        src_idx = os.path.join(bundle_root, "index")
        if os.path.isdir(src_idx):
            dst_idx = os.path.join(fm_dir, "index")
            os.makedirs(dst_idx, exist_ok=True)
            for f in os.listdir(src_idx):
                shutil.copy2(os.path.join(src_idx, f), os.path.join(dst_idx, f))

        # Copy patches
        src_patches = os.path.join(bundle_root, "patches")
        if os.path.isdir(src_patches):
            dst_patches = os.path.join(fm_dir, "patches")
            os.makedirs(dst_patches, exist_ok=True)
            for f in os.listdir(src_patches):
                shutil.copy2(os.path.join(src_patches, f), os.path.join(dst_patches, f))

        # Copy runs
        src_runs = os.path.join(bundle_root, "runs")
        if os.path.isdir(src_runs):
            dst_runs = os.path.join(fm_dir, "state", "runs")
            os.makedirs(dst_runs, exist_ok=True)
            for f in os.listdir(src_runs):
                shutil.copy2(os.path.join(src_runs, f), os.path.join(dst_runs, f))

        return manifest


# ── Inspect ────────────────────────────────────────────────────────


def inspect_bundle(bundle_path: str) -> dict[str, Any]:
    """Read bundle manifest without importing."""
    with tempfile.TemporaryDirectory() as staging:
        shutil.unpack_archive(bundle_path, staging)
        for root_dir, _, files in os.walk(staging):
            if "manifest.json" in files:
                with open(
                    os.path.join(root_dir, "manifest.json"), encoding="utf-8"
                ) as fh:
                    return json.load(fh)
    raise ValueError("Invalid bundle: no manifest.json found")


# ── Helpers ────────────────────────────────────────────────────────


def _walk_files(directory: str) -> list[str]:
    result: list[str] = []
    for dirpath, _, filenames in os.walk(directory):
        for f in filenames:
            result.append(os.path.join(dirpath, f))
    return result
