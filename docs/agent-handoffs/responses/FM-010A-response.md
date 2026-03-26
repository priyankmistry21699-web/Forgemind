TASK ID:
FM-010A

STATUS:
done

SUMMARY:
Validation and consistency pass across FM-005 through FM-010. Fixed 4 issues, confirmed 5 areas as correct, generated initial migration, and documented 6 technical debt items.

---

## VALIDATION RESULTS

### ✅ Passed (no changes needed)

1. **Enum consistency** — `TaskStatus` (7 values), `ProjectStatus` (6 values), `RunStatus` (6 values) are identical across models, schemas, and services. Schemas import enums directly from models — no duplication.

2. **Alembic metadata wiring** — `env.py` imports `Base` from `db/base.py`, which triggers all model imports. `target_metadata = Base.metadata` correctly captures all 4 tables. `sqlalchemy.url` injected at runtime from `settings.database_url`.

3. **Prompt intake → model alignment** — `plan_from_prompt()` correctly creates Project(PLANNING) → Run(PLANNING, trigger="prompt") → 3 Tasks with READY/BLOCKED/BLOCKED. Dependencies wired: task[1].depends_on=[task[0].id], task[2].depends_on=[task[1].id]. Response schema fields match service outputs.

4. **Ready-task promotion logic** — `_promote_ready_tasks()` correctly scans BLOCKED tasks in a run, checks if all `depends_on` IDs are in the completed set, and promotes to READY. State machine transitions are consistent and minimal.

5. **Task state machine** — 7 states, transitions are well-defined:
   - PENDING → READY, BLOCKED, SKIPPED
   - BLOCKED → READY, SKIPPED
   - READY → RUNNING, SKIPPED
   - RUNNING → COMPLETED, FAILED
   - FAILED → READY (retry)
   - COMPLETED, SKIPPED → terminal

---

### 🔧 Issues found and fixed

#### Issue 1: TEMP_OWNER_ID hardcoded in two route files

**Problem:** Raw `uuid.UUID("00000000-...")` constant duplicated in `projects.py` and `planner.py`. Architect flagged this as painful for auth migration.
**Fix:** Created `app/core/auth_stub.py` with `get_current_user_id()` async dependency. Both route files now use `owner_id: uuid.UUID = Depends(get_current_user_id)`. When Clerk is wired, only `auth_stub.py` changes.

#### Issue 2: Circular import risk in db/base.py

**Problem:** `base.py` defined `Base` AND imported all models at the bottom. Models imported `Base` from `base.py` — circular dependency that works by accident (Python module caching) but is fragile.
**Fix:** Split into two files:

- `db/base_class.py` — defines `Base` only (no model imports)
- `db/base.py` — imports `Base` from `base_class` + imports all models (aggregator for Alembic)
- All 4 model files now import from `base_class` instead of `base`

#### Issue 3: No initial migration file

**Problem:** Alembic was configured, models existed, but no migration was ever generated. DB schema was purely theoretical.
**Fix:** Created hand-written initial migration `alembic/versions/2026_03_26_0000_0001_initial_schema.py` that creates all 4 tables with correct column types, constraints, indexes, and enum types. Includes downgrade path.

#### Issue 4: Unused import in schemas/task.py

**Problem:** `from pydantic import BaseModel, Field` — `Field` was imported but never used.
**Fix:** Removed unused `Field` import.

---

## FILES CREATED/UPDATED

**Created:**

- apps/api/app/core/auth_stub.py — shared auth dependency stub
- apps/api/app/db/base_class.py — Base definition (no circular imports)
- apps/api/alembic/versions/2026_03_26_0000_0001_initial_schema.py — initial migration
- docs/TECHNICAL_DEBT.md — 6 documented debt items

**Updated:**

- apps/api/app/db/base.py — now aggregator module importing from base_class
- apps/api/app/models/user.py — import Base from base_class
- apps/api/app/models/project.py — import Base from base_class
- apps/api/app/models/run.py — import Base from base_class
- apps/api/app/models/task.py — import Base from base_class
- apps/api/app/api/routes/projects.py — uses get_current_user_id dependency
- apps/api/app/api/routes/planner.py — uses get_current_user_id dependency
- apps/api/app/schemas/task.py — removed unused Field import
- apps/api/README.md — updated project structure, added Local Validation section

---

## TECHNICAL DEBT DOCUMENTED (docs/TECHNICAL_DEBT.md)

| ID     | Item                               | Risk    | Summary                                                                                |
| ------ | ---------------------------------- | ------- | -------------------------------------------------------------------------------------- |
| TD-001 | depends_on ARRAY column            | Medium  | No FK integrity; migrate to junction table when orchestrator needs reverse-dep queries |
| TD-002 | SKIPPED deps ≠ satisfied           | Low–Med | Blocked tasks stay stuck if a dep is skipped; decide SKIPPED policy                    |
| TD-003 | HTTPException in services          | Low     | Couples services to HTTP; extract domain exceptions later                              |
| TD-004 | No DB-level updated_at trigger     | Low     | onupdate only works via ORM, not direct SQL                                            |
| TD-005 | No concurrency on task transitions | Low     | No row locking; add FOR UPDATE when parallel agents enabled                            |
| TD-006 | Routes not under /api/v1/ prefix   | Low     | api_v1_prefix setting exists but isn't used yet                                        |

---

## REMAINING VALIDATION (requires running infrastructure)

These cannot be verified without Postgres running. Recommended developer steps:

```bash
docker compose up -d postgres redis
make install-api
make migrate          # applies initial migration
make dev-api          # verify app starts cleanly
curl localhost:8000/health
curl localhost:8000/health/ready
```

---

ASSUMPTIONS:

- Hand-written migration matches model definitions (should be verified with `alembic check` once DB is running)
- Circular import fix doesn't change runtime behavior
- Auth stub dependency is injection-compatible with future Clerk middleware

BLOCKERS:

- None

NEXT RECOMMENDED STEP:

- FM-011: Clerk JWT authentication integration (replaces auth_stub.py)
