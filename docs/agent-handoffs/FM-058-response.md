# FM-058 — Activity Feed

## What was done

Created an immutable, chronological activity feed with 15 activity types, dual-scoped to both projects and workspaces for cross-cutting visibility into all platform operations.

## Files created

- `apps/api/app/models/activity.py` — `ActivityFeedEntry` model:
  - `actor_id` FK (indexed), `activity_type` enum (indexed), `summary` (str, max 500)
  - `project_id` FK, `workspace_id` FK for dual scoping
  - `resource_type`, `resource_id` for deep-linking
  - `metadata` (JSON), `created_at`
  - Activity type enum (15 types): `PROJECT_CREATED`, `PROJECT_UPDATED`, `RUN_STARTED`, `RUN_COMPLETED`, `RUN_FAILED`, `TASK_COMPLETED`, `ARTIFACT_CREATED`, `MEMBER_ADDED`, `MEMBER_REMOVED`, `APPROVAL_REQUESTED`, `APPROVAL_DECIDED`, `ESCALATION_TRIGGERED`, `PATCH_PROPOSED`, `PR_CREATED`, `COMMENT`
- `apps/api/app/services/activity_service.py` — Activity service:
  - `create_activity(db, ...)`: Creates immutable activity entry
  - `list_activities(db, project_id, workspace_id, limit, offset)`: Filtered listing with pagination
- `apps/api/app/api/routes/activity.py` — Routes: `POST /activity`, `GET /activity` (with project_id/workspace_id filters), `GET /workspaces/{id}/activity`
- Schemas for activity entries

## Files modified

- `apps/api/alembic/versions/2026_03_27_0019_add_collaboration_and_code_ops.py` — Creates `activity_feed_entries` table
- `apps/api/app/db/base.py` — Added `ActivityFeedEntry` import
- `apps/api/app/api/router.py` — Registered `activity_router`

## Design decisions

- Activity is immutable after creation — no edits or deletes
- Dual scoping (project + workspace) enables cross-cutting feeds at both levels
- `resource_type` + `resource_id` for deep-linking to source entities
- Chronological ordering via `created_at` — no custom sorting
- 15 types cover the full lifecycle of projects, runs, tasks, artifacts, and collaboration events
