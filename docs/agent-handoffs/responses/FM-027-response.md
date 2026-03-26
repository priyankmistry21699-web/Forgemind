# FM-027 — Run Timeline / Execution Event Log — Response

**Status:** DONE
**Date:** 2025-07-15

---

## Files Created

| File                                                                     | Purpose                                                   |
| ------------------------------------------------------------------------ | --------------------------------------------------------- |
| `apps/api/app/models/execution_event.py`                                 | ExecutionEvent model with EventType enum (10 event types) |
| `apps/api/app/schemas/execution_event.py`                                | ExecutionEventRead, ExecutionEventList Pydantic schemas   |
| `apps/api/app/services/event_service.py`                                 | emit_event, list_events service functions                 |
| `apps/api/app/api/routes/events.py`                                      | GET /events with project_id/run_id/limit/offset filters   |
| `apps/api/alembic/versions/2026_03_26_0006_0007_add_execution_events.py` | Migration 0007: execution_events table + enum + 3 indexes |

## Files Modified

| File                                         | Change                                                                                          |
| -------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| `apps/api/app/db/base.py`                    | Registered ExecutionEvent model import                                                          |
| `apps/api/app/api/router.py`                 | Mounted events router with "events" tag                                                         |
| `apps/api/app/services/execution_service.py` | Emit events at: task claimed, task completed, task failed, artifact created, approval requested |
| `apps/api/app/services/approval_service.py`  | Emit APPROVAL_RESOLVED event on approval decision                                               |

## Event Types

| Event Type         | Emitted When                                               |
| ------------------ | ---------------------------------------------------------- |
| task_claimed       | Agent claims a task via execution_service.claim_task()     |
| task_completed     | Task marked complete via execution_service.complete_task() |
| task_failed        | Task marked failed via execution_service.fail_task()       |
| artifact_created   | New artifact stored during task completion                 |
| approval_requested | Approval auto-created for architecture/review tasks        |
| approval_resolved  | Human approves/rejects an approval request                 |
| run_started        | (reserved for future use)                                  |
| run_completed      | (reserved for future use)                                  |
| run_failed         | (reserved for future use)                                  |
| plan_generated     | (reserved for future use)                                  |

## Design Decisions

1. **Inline event emission** — Events are emitted directly within service methods rather than via middleware or event bus. Simple and auditable for MVP.
2. **JSON metadata** — Each event has a `metadata_` JSON column for event-type-specific data (error messages, artifact IDs, decision details).
3. **Newest-first ordering** — Default query returns events ordered by created_at DESC.
4. **Multiple indexes** — event_type, project_id, and run_id indexes for efficient filtering.

## Technical Debt Added

- **TD-014**: No real-time event streaming (polling only)

## Acceptance Criteria Met

- [x] ExecutionEvent model with 10 event types
- [x] Events emitted at all key execution/approval points
- [x] Event query API with filtering by project/run
- [x] JSON metadata for event-specific context
- [x] Migration creates table with proper indexes
