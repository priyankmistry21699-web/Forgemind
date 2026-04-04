# FM-094 — Local Execution Sandbox

## Summary

Implemented bounded local command execution with safety controls. Provides three execution policies, a blocked-pattern list for dangerous commands, and a safe-prefix allowlist for common dev commands.

## Deliverables

### Service (`apps/local/forgemind_local/local_exec.py` — 156 lines)

- **`run_local_command(repo_root, command, timeout_s=60, policy="safe")`** — executes with safety checks
- **16 blocked patterns** — always rejected: `rm -rf /`, `rm -rf ~`, `mkfs`, `dd if=`, fork bombs, `chmod -R 777 /`, pipe-to-shell, `shutdown`, `reboot`, `format c:`, `del /f /s /q c:`, etc.
- **35 safe prefixes** — allowed under `safe` policy: pytest, ruff, black, mypy, npm test, cargo test, go test, make, cat, head, grep, git status/diff/log/show/branch, etc.
- **3 policies**:
  - `safe` — only allowlisted command prefixes
  - `permissive` — anything not in blocked list
  - `locked` — all execution blocked
- **Subprocess execution** — `shell=True`, `cwd=repo_root`, `capture_output=True`, configurable timeout
- **JSON run logging** — each execution logged to `.forgemind/state/runs/<run_id>.json`

### CLI

- **`forgemind exec "command"`** — executes and prints stdout/stderr with status

## Safety Boundaries

- `shell=True` is appropriate for a local dev tool where the user is the operator
- Blocked patterns are substring-matched defense-in-depth, not a security boundary
- Creative bypasses are possible (escaped characters, script indirection, aliases)
- `permissive` policy allows any command not in the blocked list — intentionally wide scope
- No network or filesystem sandboxing — relies on user trust
- Would be unacceptable in a multi-tenant or remote execution context

## Tests

7 tests in `TestLocalExec`:

- blocked_command, safe_command_allowed, unsafe_command_blocked_under_safe, permissive_allows_more, locked_blocks_everything, run_logging, fork_bomb_blocked

## Test Results

- **Total**: 535 passing
