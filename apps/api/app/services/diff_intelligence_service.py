"""Commit & diff intelligence — analyze diffs for impact scoring.

FM-158: Commit & Diff Intelligence.
"""

import re


def analyze_diff_stats(diff_text: str) -> dict:
    """Parse a unified diff and return file-level change stats."""
    files: list[dict] = []
    current_file: str | None = None
    additions = 0
    deletions = 0

    for line in diff_text.splitlines():
        if line.startswith("diff --git"):
            if current_file:
                files.append(
                    {"file": current_file, "additions": additions, "deletions": deletions}
                )
            match = re.search(r"b/(.+)$", line)
            current_file = match.group(1) if match else "unknown"
            additions = 0
            deletions = 0
        elif line.startswith("+") and not line.startswith("+++"):
            additions += 1
        elif line.startswith("-") and not line.startswith("---"):
            deletions += 1

    if current_file:
        files.append(
            {"file": current_file, "additions": additions, "deletions": deletions}
        )

    total_add = sum(f["additions"] for f in files)
    total_del = sum(f["deletions"] for f in files)
    total_churn = total_add + total_del

    # Impact score: Simple heuristic (normalize on 0-100 scale)
    if total_churn == 0:
        impact = 0
    elif total_churn < 50:
        impact = 20
    elif total_churn < 200:
        impact = 50
    elif total_churn < 500:
        impact = 75
    else:
        impact = 100

    return {
        "files_changed": len(files),
        "total_additions": total_add,
        "total_deletions": total_del,
        "total_churn": total_churn,
        "impact_score": impact,
        "files": files,
    }


def extract_changed_files(diff_text: str) -> list[str]:
    """Extract the list of changed file paths from a diff."""
    files = []
    for line in diff_text.splitlines():
        if line.startswith("diff --git"):
            match = re.search(r"b/(.+)$", line)
            if match:
                files.append(match.group(1))
    return files
