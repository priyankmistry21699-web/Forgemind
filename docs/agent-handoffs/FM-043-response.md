# FM-043 — Adaptive Retry / Revision Loop v2

## What was done

Built a policy-based retry and revision system that extends the Task model with retry tracking columns and provides intelligent retry decisions based on task type, exhaustion state, and configurable policies.

## Files created

- `apps/api/app/services/adaptive_retry_service.py` — Retry service:
  - `RETRY_POLICIES` dict: `standard` (3), `aggressive` (5), `conservative` (1), `no_retry` (0)
  - `TASK_TYPE_POLICIES` dict: Maps task types to default policies (e.g., `testing → aggressive`, `architecture → conservative`)
  - `get_policy_for_task(task_type)`: Returns appropriate policy name
  - `get_max_retries(policy)`: Returns max retry count for a policy
  - `can_retry(db, task)`: Returns `{can_retry, reason, retry_count, max_retries, suggested_action}` — checks status, policy, and exhaustion
  - `adaptive_retry(db, task_id)`: Increments `retry_count`, resets to `READY`, clears error/agent, emits `TASK_CLAIMED` event
  - `create_revision_task(db, failed_task_id, revision_description)`: Creates a `[Revision]` child task linked via `parent_id`
- `apps/api/app/api/routes/retry.py` — Routes: `GET /tasks/{id}/retry/check`, `POST /tasks/{id}/retry/adaptive`, `POST /tasks/{id}/revision`, `GET /runs/{id}/retry/status`
- `apps/api/alembic/versions/2026_03_28_0010_0011_add_retry_columns.py` — Migration adding 3 columns to `tasks`

## Files modified

- `apps/api/app/models/task.py` — Added columns: `retry_count` (int, default 0), `max_retries` (int, default 3), `retry_policy` (str, default `"standard"`)
- `apps/api/app/api/router.py` — Registered `retry_router` with tag `"retry"`

## Design decisions

- Policy-based approach: auto-assigns policy from task type, overridable per-task
- Suggested actions cascade: `retry → create_revision_task → escalate`
- Revision tasks linked to the original via `parent_id` FK — maintains DAG lineage
- Migration adds columns with `server_default` to handle existing rows without data migration
