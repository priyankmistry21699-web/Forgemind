TASK ID:
FM-010

STATUS:
done

SUMMARY:
Implemented Task DAG orchestration with state-machine transitions, automatic dependency promotion, and ready-task selection. Includes task schemas, service layer with validation, and four endpoints for listing/querying/transitioning tasks. When a task completes, blocked downstream tasks are automatically promoted to READY if all their dependencies are satisfied.

FILES CHANGED:

- apps/api/app/schemas/task.py (created — TaskRead, TaskList, TaskStatusUpdate, ReadyTasksResponse)
- apps/api/app/services/task_service.py (created — get, list_by_run, update_status, get_ready, \_promote_ready)
- apps/api/app/api/routes/tasks.py (created — GET list, GET ready, GET by ID, PATCH status)
- apps/api/app/api/router.py (updated — registered tasks_router)
- apps/api/README.md (updated — endpoint table)

IMPLEMENTATION NOTES:

- State machine enforces valid transitions:
  - PENDING → READY, BLOCKED, SKIPPED
  - BLOCKED → READY, SKIPPED
  - READY → RUNNING, SKIPPED
  - RUNNING → COMPLETED, FAILED
  - FAILED → READY (retry)
  - COMPLETED/SKIPPED → terminal (no transitions)
- \_promote_ready_tasks: after a task completes, queries all BLOCKED tasks in the same run and promotes any whose depends_on list is fully satisfied
- GET /runs/{run_id}/tasks/ready returns only READY tasks — this is the query the orchestrator will poll
- 409 Conflict returned for invalid state transitions
- Tasks ordered by order_index for deterministic display

ASSUMPTIONS:

- ARRAY-based depends_on is sufficient for current scale (no junction table needed)
- Promotion runs synchronously within the same request (no background job yet)
- No concurrency locking on status transitions — acceptable for single-agent runs
- The orchestrator (future phase) will poll /tasks/ready to pick up work

BLOCKERS:

- None

NEXT RECOMMENDED STEP:

- FM-011: Authentication (Clerk JWT integration + RBAC middleware)
