# FM-032 — Execution Control Actions (Retry / Cancel)

## Status: DONE

## What was implemented

### Backend

1. **`apps/api/app/services/execution_service.py`** — Added two new functions:
   - `retry_task(db, task_id)`: Validates FAILED status, resets to READY, clears error_message and assigned_agent_slug, emits TASK_CLAIMED event with `{"action": "retry"}` metadata
   - `cancel_task(db, task_id)`: Validates READY or RUNNING status, sets to SKIPPED with error_message "Cancelled by operator", emits TASK_FAILED event with `{"action": "cancel"}` metadata
2. **`apps/api/app/api/routes/tasks.py`** — Added two new endpoints:
   - `POST /tasks/{task_id}/retry`
   - `POST /tasks/{task_id}/cancel`

### Frontend

3. **`apps/web/lib/tasks.ts`** — Added `retryTask(taskId)` and `cancelTask(taskId)` API helpers
4. **`apps/web/components/tasks/run-task-list.tsx`** — Added:
   - Retry button (indigo, shown for failed tasks)
   - Cancel button (red, shown for ready/running tasks)
   - Auto-refresh after actions via `refreshKey` state
   - Error message display for failed tasks

## Technical debt

- TD-016: Retry/cancel reuse existing event types (TASK_CLAIMED/TASK_FAILED) with action metadata instead of dedicated enum values
