"""Commit & diff intelligence — analyze diffs for impact scoring and risk rules.

FM-158: Commit & Diff Intelligence.
"""

import re


# ── Risk Rules ───────────────────────────────────────────────────

_RISK_RULES: list[dict] = [
    {
        "id": "LARGE_FILE_CHANGE",
        "description": "Single file has > 300 lines changed",
        "severity": "high",
    },
    {
        "id": "MIGRATION_DETECTED",
        "description": "Database migration file modified",
        "severity": "high",
        "pattern": r"(migrations?/|alembic/|schema\.sql)",
    },
    {
        "id": "SECRET_PATTERN",
        "description": "Potential secret or credential in diff",
        "severity": "critical",
        "pattern": r"(api[_-]?key|secret|password|token)\s*[:=]\s*['\"]",
    },
    {
        "id": "CI_CONFIG_CHANGE",
        "description": "CI/CD configuration file modified",
        "severity": "medium",
        "pattern": r"(\.github/workflows/|\.gitlab-ci|Jenkinsfile|\.circleci)",
    },
    {
        "id": "DEPENDENCY_CHANGE",
        "description": "Dependency manifest file modified",
        "severity": "medium",
        "pattern": r"(requirements.*\.txt|pyproject\.toml|package\.json|Cargo\.toml|go\.mod)",
    },
    {
        "id": "DOCKERFILE_CHANGE",
        "description": "Container configuration modified",
        "severity": "medium",
        "pattern": r"(Dockerfile|docker-compose|\.dockerignore)",
    },
    {
        "id": "SECURITY_FILE",
        "description": "Security-sensitive file modified",
        "severity": "high",
        "pattern": r"(auth|permission|rbac|crypto|ssl|tls|encryption)",
    },
    {
        "id": "TEST_DELETION",
        "description": "Test file has more deletions than additions",
        "severity": "medium",
        "pattern": r"(test_|_test\.|spec\.|\.test\.)",
    },
]


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


def evaluate_risk_rules(diff_text: str) -> list[dict]:
    """Evaluate risk rules against a diff and return triggered rules (FM-158).

    Returns a list of triggered risk items with file, rule, and severity info.
    """
    stats = analyze_diff_stats(diff_text)
    triggered: list[dict] = []

    files = stats["files"]

    for file_info in files:
        filepath = file_info["file"]
        churn = file_info["additions"] + file_info["deletions"]

        # LARGE_FILE_CHANGE
        if churn > 300:
            triggered.append({
                "rule_id": "LARGE_FILE_CHANGE",
                "severity": "high",
                "file": filepath,
                "detail": f"{churn} lines changed in single file",
            })

        # Pattern-based rules
        for rule in _RISK_RULES:
            pattern = rule.get("pattern")
            if not pattern:
                continue
            if re.search(pattern, filepath, re.IGNORECASE):
                item = {
                    "rule_id": rule["id"],
                    "severity": rule["severity"],
                    "file": filepath,
                    "detail": rule["description"],
                }
                # TEST_DELETION: only trigger if deletions > additions
                if rule["id"] == "TEST_DELETION":
                    if file_info["deletions"] > file_info["additions"]:
                        triggered.append(item)
                else:
                    triggered.append(item)

    # SECRET_PATTERN: scan added lines
    secret_rule = next((r for r in _RISK_RULES if r["id"] == "SECRET_PATTERN"), None)
    if secret_rule:
        for line in diff_text.splitlines():
            if line.startswith("+") and not line.startswith("+++"):
                if re.search(secret_rule["pattern"], line, re.IGNORECASE):
                    triggered.append({
                        "rule_id": "SECRET_PATTERN",
                        "severity": "critical",
                        "file": "(added line)",
                        "detail": "Potential secret or credential detected in added line",
                    })
                    break  # report once

    # Compute overall risk score
    severity_weights = {"critical": 40, "high": 20, "medium": 10, "low": 5}
    risk_score = min(
        100,
        sum(severity_weights.get(t["severity"], 5) for t in triggered),
    )

    return {
        "risk_score": risk_score,
        "risk_level": (
            "critical" if risk_score >= 60
            else "high" if risk_score >= 30
            else "medium" if risk_score >= 10
            else "low"
        ),
        "triggered_rules": triggered,
        "total_triggers": len(triggered),
        "stats": stats,
    }


def get_risk_rules() -> list[dict]:
    """Return the list of available risk rules."""
    return [
        {"id": r["id"], "description": r["description"], "severity": r["severity"]}
        for r in _RISK_RULES
    ]
