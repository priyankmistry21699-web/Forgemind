"""FM-094 — Local execution sandbox orchestration.

Provides bounded, reviewable local command execution with safety controls.
"""

from __future__ import annotations

import datetime as _dt
import json
import os
import subprocess
import time
import uuid
from typing import Any

# ── Safety policy ──────────────────────────────────────────────────

# Commands that are always blocked regardless of policy
_BLOCKED_PATTERNS = [
    "rm -rf /",
    "rm -rf ~",
    "rm -rf $HOME",
    "mkfs",
    "dd if=",
    ":(){",  # fork bomb
    "chmod -R 777 /",
    "curl | sh",
    "curl | bash",
    "wget | sh",
    "wget | bash",
    "> /dev/sda",
    "shutdown",
    "reboot",
    "halt",
    "poweroff",
    "format c:",
    "del /f /s /q c:",
]

# Commands allowed under "safe" policy
_SAFE_PREFIXES = [
    "pytest",
    "python -m pytest",
    "python -m",
    "ruff",
    "black",
    "mypy",
    "flake8",
    "isort",
    "npm test",
    "npm run lint",
    "npm run build",
    "npm run format",
    "npx tsc",
    "npx eslint",
    "npx prettier",
    "cargo test",
    "cargo build",
    "cargo clippy",
    "go test",
    "go build",
    "go vet",
    "make test",
    "make lint",
    "make build",
    "make check",
    "cat ",
    "head ",
    "tail ",
    "wc ",
    "grep ",
    "find ",
    "ls ",
    "dir ",
    "git status",
    "git diff",
    "git log",
    "git show",
    "git branch",
]


def _is_blocked(command: str) -> str | None:
    """Return reason if command is always blocked, else None."""
    cmd_lower = command.lower().strip()
    for pat in _BLOCKED_PATTERNS:
        if pat in cmd_lower:
            return f"Matches blocked pattern: {pat}"
    return None


def _is_allowed_safe(command: str) -> bool:
    """Check if command is allowed under 'safe' execution policy."""
    cmd_stripped = command.strip()
    return any(cmd_stripped.startswith(prefix) for prefix in _SAFE_PREFIXES)


# ── Execution ──────────────────────────────────────────────────────


def run_local_command(
    repo_root: str,
    command: str,
    *,
    timeout_s: int = 60,
    policy: str = "safe",
) -> dict[str, Any]:
    """Execute a bounded local command.

    Returns dict with keys:
        run_id, command, blocked, reason, stdout, stderr,
        returncode, duration_s, logged_at
    """
    run_id = str(uuid.uuid4())
    result: dict[str, Any] = {
        "run_id": run_id,
        "command": command,
        "blocked": False,
        "reason": "",
        "stdout": "",
        "stderr": "",
        "returncode": -1,
        "duration_s": 0.0,
        "logged_at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
    }

    # 1. Check always-blocked
    block_reason = _is_blocked(command)
    if block_reason:
        result["blocked"] = True
        result["reason"] = block_reason
        _log_run(repo_root, result)
        return result

    # 2. Check policy
    if policy == "locked":
        result["blocked"] = True
        result["reason"] = "Execution policy is 'locked'."
        _log_run(repo_root, result)
        return result

    if policy == "safe" and not _is_allowed_safe(command):
        result["blocked"] = True
        result["reason"] = (
            "Command not in safe allow-list. "
            "Change execution_policy to 'permissive' or use a recognised command."
        )
        _log_run(repo_root, result)
        return result

    # 3. Execute
    start = time.monotonic()
    try:
        proc = subprocess.run(
            command,
            shell=True,
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
        result["stdout"] = proc.stdout
        result["stderr"] = proc.stderr
        result["returncode"] = proc.returncode
    except subprocess.TimeoutExpired:
        result["stderr"] = f"Command timed out after {timeout_s}s"
        result["returncode"] = -1
    except Exception as exc:
        result["stderr"] = str(exc)
        result["returncode"] = -1

    result["duration_s"] = round(time.monotonic() - start, 3)
    _log_run(repo_root, result)
    return result


# ── Run logging ────────────────────────────────────────────────────


def _log_run(repo_root: str, result: dict[str, Any]) -> None:
    """Persist execution record to .forgemind/state/runs/."""
    log_dir = os.path.join(repo_root, ".forgemind", "state", "runs")
    os.makedirs(log_dir, exist_ok=True)
    path = os.path.join(log_dir, f"{result['run_id']}.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2, default=str)


def list_runs(repo_root: str) -> list[dict[str, Any]]:
    """List all logged local execution runs."""
    log_dir = os.path.join(repo_root, ".forgemind", "state", "runs")
    if not os.path.isdir(log_dir):
        return []
    runs: list[dict[str, Any]] = []
    for fname in sorted(os.listdir(log_dir)):
        if fname.endswith(".json"):
            with open(os.path.join(log_dir, fname), encoding="utf-8") as fh:
                runs.append(json.load(fh))
    return runs
