# FM-055 — Notification Engine

## What was done

Created a per-user notification inbox with 12 notification types and 4 priority levels, supporting resource deep-linking and bulk read operations.

## Files created

- `apps/api/app/models/notification.py` — `Notification` model:
  - `user_id` FK (indexed), `notification_type` enum (indexed), `priority` enum
  - `title`, `body`, `is_read` (bool, default False)
  - `resource_type`, `resource_id` for deep-linking to source entities
  - `metadata` (JSON), `created_at`
  - Notification type enum (12 types): `TASK_ASSIGNED`, `TASK_COMPLETED`, `APPROVAL_REQUIRED`, `APPROVAL_GRANTED`, `APPROVAL_DENIED`, `RUN_STARTED`, `RUN_COMPLETED`, `RUN_FAILED`, `MEMBER_ADDED`, `MEMBER_REMOVED`, `ESCALATION`, `SYSTEM`
  - Priority enum: `LOW`, `NORMAL` (default), `HIGH`, `URGENT`
- `apps/api/app/services/notification_service.py` — Notification service:
  - `create_notification()`: Creates notification with type, priority, and resource link
  - `list_notifications(user_id, unread_only)`: Filtered listing with optional unread filter
  - `mark_notification_read(notification_id)`: Marks single notification as read
  - `mark_all_read(user_id)`: Bulk mark-all-read, returns count
- `apps/api/app/api/routes/notifications.py` — Routes: `POST /notifications`, `GET /notifications` (with `unread_only` filter), `POST /notifications/{id}/read`, `POST /notifications/read-all`
- Schemas for notification CRUD

## Files modified

- `apps/api/alembic/versions/2026_03_27_0019_add_collaboration_and_code_ops.py` — Creates `notifications` table
- `apps/api/app/db/base.py` — Added `Notification` import
- `apps/api/app/api/router.py` — Registered `notifications_router`

## Design decisions

- Per-user notification inbox with `user_id` indexed for fast queries
- Resource links (`resource_type` + `resource_id`) enable deep-linking from notification to source entity
- Read status tracked at notification level (not conversation level)
- Unread count computed per list call rather than cached separately
