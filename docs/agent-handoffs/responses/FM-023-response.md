# FM-023 — Execution Service (Claim/Complete/Fail) — Response

**Status:** DONE
**Date:** 2025-07-15

---

## Files Created

| File                                                                           | Purpose                                              |
| ------------------------------------------------------------------------------ | ---------------------------------------------------- |
| `apps/api/app/services/execution_service.py`                                   | claim_task, complete_task, fail_task logic           |
| `apps/api/alembic/versions/2026_03_26_0004_0005_add_task_execution_columns.py` | Migration 0005 — assigned_agent_slug + error_message |

## Files Modified

| File                               | Change                                                                |
| ---------------------------------- | --------------------------------------------------------------------- |
| `apps/api/app/models/task.py`      | Added assigned_agent_slug (String 50) and error_message (Text) fields |
| `apps/api/app/schemas/task.py`     | Added fields to TaskRead + 3 new request schemas                      |
| `apps/api/app/api/routes/tasks.py` | Added POST claim/complete/fail routes                                 |

## Design Decisions

1. **State machine enforcement**: claim_task validates task is READY, complete/fail validate task is RUNNING. Prevents double-claim or completing an unclaimed task.
2. **assigned_agent_slug** instead of FK to agents table — keeps execution tracking lightweight and decoupled from agent lifecycle.
3. **Optional artifact creation in complete_task** — not every task completion produces an artifact (e.g., review tasks might just report pass/fail).
4. **\_promote_ready_tasks()** called after completion — automatically advances dependent tasks from PENDING to READY when all their dependencies are met.
5. **Separate error session pattern** — fail_task uses its own DB session context to ensure failure state is persisted even if the calling transaction rolls back.

## Acceptance Criteria Met

- [x] claim_task validates READY state, sets RUNNING + assigned_agent_slug
- [x] complete_task validates RUNNING, optionally creates artifact, sets COMPLETED
- [x] complete_task triggers \_promote_ready_tasks() for DAG progression
- [x] fail_task validates RUNNING, stores error_message, sets FAILED
- [x] Three new API routes: POST /tasks/{id}/claim, /complete, /fail
- [x] TaskClaimRequest, TaskCompleteRequest, TaskFailRequest schemas
- [x] Migration 0005 adds execution columns
