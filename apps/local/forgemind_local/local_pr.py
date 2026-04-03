"""FM-096 — Local PR preparation workflow.

Generates review-ready PR materials from the local git diff without
requiring any remote write access.
"""

from __future__ import annotations

import re
import subprocess
from typing import Any


def _git(repo_root: str, *args: str) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        capture_output=True,
        text=True,
        timeout=30,
    )
    return proc.stdout.strip()


# ── Diff analysis helpers ──────────────────────────────────────────


def _changed_files(repo_root: str, base: str) -> list[dict[str, Any]]:
    """Get list of changed files with stats vs *base* branch."""
    raw = _git(repo_root, "diff", "--stat", "--numstat", base)
    files: list[dict[str, Any]] = []
    for line in raw.splitlines():
        parts = line.split("\t")
        if len(parts) == 3:
            added, removed, path = parts
            files.append(
                {
                    "path": path,
                    "added": int(added) if added.isdigit() else 0,
                    "removed": int(removed) if removed.isdigit() else 0,
                }
            )
    return files


def _classify_change(path: str) -> str:
    """Classify a file change into a subsystem category."""
    p = path.lower()
    if "test" in p:
        return "Tests"
    if "/routes/" in p or "/api/" in p:
        return "API"
    if "/services/" in p:
        return "Services"
    if "/models/" in p:
        return "Models"
    if "/schemas/" in p:
        return "Schemas"
    if "/core/" in p:
        return "Core"
    if "alembic" in p or "migration" in p:
        return "Migrations"
    if p.endswith((".ts", ".tsx", ".js", ".jsx", ".css", ".scss")):
        return "Frontend"
    if p.endswith((".yml", ".yaml", ".toml", ".json", ".cfg")):
        return "Config"
    if p.endswith(".md"):
        return "Docs"
    return "Other"


def _risk_notes(files: list[dict[str, Any]]) -> list[str]:
    """Generate risk notes from changed files."""
    risks: list[str] = []
    for f in files:
        p = f["path"]
        if "migration" in p.lower() or "alembic" in p.lower():
            risks.append(f"Database migration changed: `{p}` — verify rollback safety")
        if "/core/" in p and ("auth" in p.lower() or "security" in p.lower()):
            risks.append(f"Security-sensitive file changed: `{p}`")
        if f["added"] + f["removed"] > 200:
            risks.append(f"Large change in `{p}` (+{f['added']}/-{f['removed']})")
    if not risks:
        risks.append("No elevated risks detected.")
    return risks


def _test_checklist(files: list[dict[str, Any]]) -> list[str]:
    """Generate a test checklist based on changed areas."""
    areas = {_classify_change(f["path"]) for f in files}
    checklist: list[str] = []
    if "API" in areas or "Services" in areas:
        checklist.append("- [ ] Run backend tests: `pytest --tb=short -q`")
    if "Frontend" in areas:
        checklist.append("- [ ] Run frontend typecheck: `npx tsc --noEmit`")
        checklist.append("- [ ] Run frontend lint: `npm run lint`")
    if "Models" in areas or "Migrations" in areas:
        checklist.append("- [ ] Verify migration applies cleanly")
    if "Config" in areas:
        checklist.append("- [ ] Verify CI config changes")
    if not checklist:
        checklist.append("- [ ] Run full test suite")
    return checklist


# ── PR markdown generation ─────────────────────────────────────────


def prepare_pr(repo_root: str, *, base_branch: str = "main") -> dict[str, Any]:
    """Generate PR summary, body, checklist, and risk notes.

    Returns dict with keys: markdown, title, files, risks, checklist, subsystems.
    """
    current_branch = _git(repo_root, "rev-parse", "--abbrev-ref", "HEAD")
    commit_log = _git(
        repo_root, "log", f"{base_branch}..HEAD", "--oneline", "--no-decorate"
    )
    files = _changed_files(repo_root, base_branch)

    # Subsystem breakdown
    subsystems: dict[str, list[str]] = {}
    for f in files:
        cat = _classify_change(f["path"])
        subsystems.setdefault(cat, []).append(f["path"])

    total_added = sum(f["added"] for f in files)
    total_removed = sum(f["removed"] for f in files)
    risks = _risk_notes(files)
    checklist = _test_checklist(files)

    # Title suggestion from branch name / commits
    title = current_branch.replace("-", " ").replace("_", " ").title()
    if commit_log:
        first_commit = commit_log.splitlines()[0]
        # Strip hash
        title = re.sub(r"^[0-9a-f]+ ", "", first_commit)

    # Build markdown
    parts: list[str] = []
    parts.append(f"## {title}\n")
    parts.append(f"**Branch:** `{current_branch}` → `{base_branch}`\n")
    parts.append(
        f"**Files changed:** {len(files)}  |  **+{total_added}** / **-{total_removed}**\n"
    )

    if commit_log:
        parts.append("### Commits\n")
        for line in commit_log.splitlines()[:20]:
            parts.append(f"- {line}")
        parts.append("")

    parts.append("### Changed Subsystems\n")
    for cat, paths in sorted(subsystems.items()):
        parts.append(f"**{cat}** ({len(paths)} files)")
        for p in paths[:10]:
            parts.append(f"- `{p}`")
        if len(paths) > 10:
            parts.append(f"- … and {len(paths) - 10} more")
        parts.append("")

    parts.append("### Risk Analysis\n")
    for r in risks:
        parts.append(f"- {r}")
    parts.append("")

    parts.append("### Test Checklist\n")
    parts.extend(checklist)
    parts.append("")

    markdown = "\n".join(parts)

    return {
        "markdown": markdown,
        "title": title,
        "branch": current_branch,
        "base": base_branch,
        "files": files,
        "risks": risks,
        "checklist": checklist,
        "subsystems": subsystems,
    }
