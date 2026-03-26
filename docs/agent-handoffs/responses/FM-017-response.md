# FM-017 Response — Planner Result Persistence Model and API

## Status: COMPLETE

---

## Files Created

| File                                                                    | Purpose                                         |
| ----------------------------------------------------------------------- | ----------------------------------------------- |
| `apps/api/app/models/planner_result.py`                                 | `PlannerResult` SQLAlchemy model (1:1 with Run) |
| `apps/api/app/schemas/planner_result.py`                                | `PlannerResultRead` Pydantic schema             |
| `apps/api/app/api/routes/planner_results.py`                            | `GET /runs/{run_id}/plan` endpoint              |
| `apps/api/alembic/versions/2026_03_26_0001_0002_add_planner_results.py` | Migration adding `planner_results` table        |

## Files Modified

| File                                       | Change                                                                  |
| ------------------------------------------ | ----------------------------------------------------------------------- |
| `apps/api/app/models/run.py`               | Added `planner_result` relationship (one-to-one, cascade delete)        |
| `apps/api/app/db/base.py`                  | Registered `PlannerResult` import for Alembic metadata                  |
| `apps/api/app/services/planner_service.py` | Returns 4-tuple now; creates stub `PlannerResult` with placeholder data |
| `apps/api/app/api/routes/planner.py`       | Updated to destructure 4-tuple from `plan_from_prompt()`                |
| `apps/api/app/api/router.py`               | Registered `planner_results_router`                                     |

---

## PlannerResult Model

| Column                 | Type              | Notes                              |
| ---------------------- | ----------------- | ---------------------------------- |
| `id`                   | UUID PK           | Auto-generated                     |
| `run_id`               | UUID FK → runs.id | Unique (one result per run)        |
| `overview`             | Text              | High-level planning summary        |
| `architecture_summary` | Text              | Architecture description           |
| `recommended_stack`    | JSON              | Dict of tech stack recommendations |
| `assumptions`          | JSON              | List of planning assumptions       |
| `next_steps`           | JSON              | List of next actions               |
| `created_at`           | DateTime(tz)      | Server default                     |
| `updated_at`           | DateTime(tz)      | Server default + onupdate          |

---

## API Endpoint

- `GET /runs/{run_id}/plan` → returns `PlannerResultRead` or 404

---

## Planner Service Update

`plan_from_prompt()` now returns `(project, run, tasks, planner_result)`. The planner result is populated with stub data that will be replaced by real LLM output in FM-020.

---

## Technical Debt: None introduced
