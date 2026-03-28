# FM-061 — Repo Sync Metadata

## What was done

Enhanced the RepoConnection model with sync lifecycle tracking — SyncStatus enum, commit SHA tracking, provider metadata, and dedicated service methods + API endpoints for sync status inspection and refresh.

## Files modified

- `apps/api/app/models/repo_connection.py` — Added `SyncStatus` enum (IDLE, SYNCING, SUCCESS, FAILED) and `BranchMode` enum (DIRECT, FEATURE_BRANCH, REVIEW_BRANCH). Added 10 new columns: `base_branch`, `target_branch`, `linked_paths` (JSON), `last_sync_status` (SyncStatus enum), `last_sync_error`, `last_synced_commit`, `provider_metadata` (JSON), `branch_mode` (BranchMode enum), `target_branch_template`, `last_generated_branch`.
- `apps/api/app/schemas/repo.py` — Added all new fields to `RepoConnectionRead`, `RepoConnectionCreate`, `RepoConnectionUpdate`. Added new schemas: `RepoSyncMetadata` (sync_status, last_synced_commit, last_sync_error, last_synced_at, provider_metadata).
- `apps/api/app/services/repo_service.py` — Added `refresh_sync_metadata(db, connection_id)` (reads local git repo to extract HEAD commit, branch info, sets sync status) and `get_sync_status(db, connection_id)` (returns current sync metadata).
- `apps/api/app/api/routes/repos.py` — Added `GET /repos/{id}/sync-status` and `POST /repos/{id}/refresh-sync` endpoints. Updated `create_connection` to pass new fields.
- `apps/api/alembic/versions/2026_03_31_0021_add_code_ops_enhancements.py` — New migration adding all columns and enum types.

## Design decisions

- SyncStatus is a separate enum from the existing connection `status` (CONNECTED/DISCONNECTED/etc.) — sync state is orthogonal to connection health
- `last_synced_commit` stores the full SHA for reliable comparison during incremental syncs
- `provider_metadata` is a flexible JSON column for provider-specific data (GitHub rate limits, GitLab pipeline status, etc.)
- `refresh_sync_metadata` reads from local git directory when `workspace_path` is set; gracefully falls back to error state
