# FM-040 — Adaptive Execution Loop v1

## What was done

Created an adaptive orchestrator that transitions ForgeMind from a linear task executor to a system that reacts to failures, approval rejections, and execution context.

## Files created

- `apps/api/app/services/adaptive_orchestrator.py` — Full adaptive orchestration:
  - `select_next_tasks(db, max_tasks)`: Priority-based task selection:
    1. Failed tasks eligible for auto-retry (retry_count < 2)
    2. Critical task types (architecture, codegen) that are READY
    3. Remaining READY tasks by order_index
  - `auto_retry_task(db, task)`: Auto-retry with agent re-routing — resets failed task to READY, optionally assigns a different agent via composition service
  - `handle_approval_rejections(db)`: Detects rejected approvals and requeues associated tasks for rework with rejection context
  - `run_adaptive_cycle(db, max_tasks)`: Single orchestration cycle combining all adaptive behaviors

## Files modified

- `apps/worker/worker/main.py` — Replaced static READY-task polling with adaptive orchestration:
  - Worker now calls `adaptive_orchestrator.run_adaptive_cycle()` each cycle
  - Approval rejections are handled before task selection
  - Failed tasks are auto-retried before new tasks are picked up
  - Logging shows adaptive actions (requeued, retried) per cycle

## Design decisions

- Max 2 auto-retries before leaving task failed (prevents infinite retry loops)
- Retry count tracked via `[retry N]` suffix in error_message (no schema change needed)
- Agent re-routing on retry uses composition_service with no hint (ignores previous agent)
- Approval rejection requeue only affects COMPLETED tasks (rejection = rework needed)
- Critical task types prioritized to unblock downstream work faster
- Worker loop is backward compatible — still processes READY tasks normally after adaptive pre-processing
