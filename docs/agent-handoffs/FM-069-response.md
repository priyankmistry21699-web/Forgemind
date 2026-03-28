# FM-069 — Code Execution Sandbox

## What was done

Added safe code execution with command allowlisting, shell injection prevention, timeout enforcement, and output capture. Enhanced SandboxExecution model with safety fields. Built frontend sandbox viewer.

## Files modified

- `apps/api/app/models/code_ops.py` — Added 4 new columns to SandboxExecution: `approval_id` (FK to repo_action_approvals, nullable), `allowed_commands` (JSON list), `resource_limits` (JSON dict), `isolated` (boolean, default True).
- `apps/api/app/schemas/code_ops.py` — Added new fields to SandboxExecution Create/Read schemas. Added `SandboxRunRequest` schema (execution_id: UUID).
- `apps/api/app/services/code_ops_service.py` — Added:
  - `SANDBOX_COMMAND_ALLOWLIST`: python, python3, pip, pytest, echo, cat, ls, dir, pwd, whoami, date, head, tail, wc, grep, find
  - `MAX_SANDBOX_TIMEOUT`: 300 seconds
  - `_validate_command(command)`: Splits command, validates base command against allowlist, blocks shell injection patterns (&&, ||, ;, |, `, $( , ${, >, <)
  - `run_sandbox_execution(db, execution_id)`: Full execution pipeline — validates command, creates subprocess via `asyncio.create_subprocess_exec`, enforces timeout via `asyncio.wait_for`, captures stdout/stderr, records exit code and duration, handles timeout/error states
  - Updated `create_sandbox_execution()` with FM-069 safety fields
- `apps/api/app/api/routes/code_ops.py` — Added `POST /sandbox/run` endpoint.

## Files created

- `apps/web/app/dashboard/sandbox/page.tsx` — Sandbox viewer with:
  - Command runner input with allowlist notice
  - Execution list (command, status badge, exit code, timestamp)
  - Execution detail panel (stdout in green, stderr in red, metadata)
  - Status badges (pending, running, success, failed, timeout, blocked)

## Design decisions

- **Command allowlist over blocklist** — safer default; only explicitly permitted commands can execute
- **Shell injection prevention** — blocks `&&`, `||`, `;`, `|`, backticks, `$(`, `${`, `>`, `<` in command strings
- **No shell=True** — uses `asyncio.create_subprocess_exec` (not `shell=True`) to prevent shell interpretation
- **Timeout enforcement** — `asyncio.wait_for` with configurable timeout; process killed on timeout
- **Output capture** — stdout and stderr captured separately via `communicate()` with decode('utf-8', errors='replace')
- **Host-level execution** — commands run on the host OS (no container isolation); TD-022 tracks containerization as future work
- **`isolated` flag** — stored on model for future container isolation toggle; currently informational
