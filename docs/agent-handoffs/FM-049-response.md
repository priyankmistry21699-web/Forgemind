# FM-049 — External Repo Integration + Audit Export

## What was done

Added external repository connection management (GitHub, GitLab, Bitbucket, local) with health checks and sync tracking, plus a full audit export system producing JSON and CSV outputs with composable filters.

## Files created

### Repo Connection
- `apps/api/app/models/repo_connection.py` — `RepoConnection` model:
  - `RepoProvider` enum: `GITHUB`, `GITLAB`, `BITBUCKET`, `LOCAL`
  - `RepoConnectionStatus` enum: `CONNECTED`, `DISCONNECTED`, `ERROR`, `PENDING`
  - FK to project (CASCADE), `repo_url`, `repo_name`, `default_branch`
  - `credential_env_key` (references vault), `config` (JSON), `workspace_path` (for local repos), `last_synced_at`
- `apps/api/app/services/repo_service.py` — Repo service:
  - Full CRUD: `create_connection`, `get_connection`, `list_connections`, `update_connection`, `delete_connection`
  - `check_connection_health()`: Validates credential env var + URL reachability
  - `sync_connection()`: Updates `last_synced_at` + status
- `apps/api/app/api/routes/repos.py` — Routes: `POST /projects/{id}/repos`, `GET /projects/{id}/repos`, `GET /repos/{id}`, `PATCH /repos/{id}`, `DELETE /repos/{id}`, `POST /repos/{id}/sync`, `GET /repos/{id}/health`
- `apps/api/app/schemas/repo.py` — Read/create/update schemas
- `apps/api/alembic/versions/2026_03_30_0018_add_repo_connections.py` — Migration creating `repo_connections`

### Audit Export
- `apps/api/app/services/audit_export_service.py` — Audit service:
  - `_fetch_events(db, ...)`: Filtered event queries (project, run, type, date range)
  - `export_events_json(db, ...)`: JSON with `export_metadata` + events array
  - `export_events_csv(db, ...)`: CSV string with headers
  - `get_audit_summary(db, ...)`: Event type breakdown counts
- `apps/api/app/api/routes/audit.py` — Routes: `GET /audit/export/json`, `GET /audit/export/csv`, `GET /audit/summary`

## Files modified

- `apps/api/app/db/base.py` — Added `RepoConnection` import
- `apps/api/app/api/router.py` — Registered `repos_router` and `audit_router`

## Design decisions

- Repo credentials referenced by env var key (not stored in DB) — consistent with vault pattern from FM-042
- `LOCAL` provider supports filesystem workspace paths for local development
- Audit CSV export uses `PlainTextResponse` with `Content-Disposition: attachment` header
- Audit export filters are composable (all optional query params)
