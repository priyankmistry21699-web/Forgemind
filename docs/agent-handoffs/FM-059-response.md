# FM-059 — User Presence & Activity Tracking

## What was done

Added lightweight user presence tracking with one record per user (upsert pattern), enabling "who's viewing what" visibility and providing rich context for task assignment decisions.

## Files created

- `apps/api/app/models/activity.py` — Added `UserPresence` model (same file as `ActivityFeedEntry`):
  - `user_id` FK (unique, indexed) — one presence record per user
  - `status` (str, max 20) — flexible status field (not a fixed enum)
  - `current_resource_type`, `current_resource_id` — what the user is currently viewing
  - `last_seen_at` (timestamp)
- `apps/api/app/services/user_activity_service.py` — User activity service:
  - `touch_user_activity(db, user_id, resource_type, resource_id)`: Updates `last_seen_at` and current resource
  - `get_active_users_on_resource(db, resource_type, resource_id)`: Lists users currently viewing a specific resource
  - `get_user_assignment_context(db, user_id)`: Full context dict for assignment logic (presence + recent activity)

## Files modified

- `apps/api/app/services/activity_service.py` — Added presence functions: `upsert_presence()`, `get_presence()`, `list_presence()`
- `apps/api/alembic/versions/2026_03_27_0019_add_collaboration_and_code_ops.py` — Creates `user_presences` table
- `apps/api/app/api/routes/activity.py` — Added presence routes: `PUT /presence`, `GET /presence`, `GET /presence/{user_id}`

## Design decisions

- One presence record per user (unique constraint) — upsert pattern avoids duplicates
- Lightweight tracking: only last-seen timestamp and current resource, not full session history
- `status` is a flexible string (not enum) to support future status types without migrations
- `touch_user_activity()` designed for middleware hooks — updates presence on every request
- `get_user_assignment_context()` provides rich decision context for intelligent task routing
