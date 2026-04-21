# 7 · Change Guide

> "I need to change X — where do I start?" Follow the recipe, then run the tests listed.

## Index

- [Backend](#backend)
- [Frontend](#frontend)
- [Integrations](#integrations)
- [SDKs](#sdks)
- [Tests](#tests)
- [Docs](#docs)
- [Migrations & models](#migrations--models)
- [Config / env vars](#config--env-vars)
- [CI / tooling](#ci--tooling)

---

## Backend

### Add a new API route

1. Create `apps/api/app/api/routes/<domain>.py` with an `APIRouter` and thin handlers.
2. Register it in [`apps/api/app/api/routes/__init__.py`](../../apps/api/app/api/routes/__init__.py) (`api_router.include_router(...)` with a `prefix="/..."` under `/api/v1/`).
3. Add request/response schemas in `apps/api/app/schemas/<domain>.py` (Pydantic v2).
4. Implement business logic in `apps/api/app/services/<domain>_service.py`.
5. Add route-level tests under `apps/api/tests/` (use the `session` fixture from `conftest.py`).
6. Run `cd apps/api && pytest`.

> Rule: routes do validation + authz + one service call. If the handler has more than ~10 lines of logic, it belongs in a service.

### Add a new service

1. `apps/api/app/services/<name>_service.py` — async functions that take an `AsyncSession`.
2. Use `select(Model).where(...)` (SQLAlchemy 2 style). Never raw SQL.
3. Return Pydantic schemas or dataclasses, not ORM instances (avoid leakage into routes).
4. If it calls an LLM, route through [`core/llm.py`](../../apps/api/app/core/llm.py) so costs are recorded.
5. If it emits user-visible events, call [`event_service.record()`](../../apps/api/app/services/event_service.py) (which fans out to `stream_service`).

### Change existing business logic

1. Find the route → service: see [BACKEND_GRAPH.md](BACKEND_GRAPH.md) "Route → service adjacency".
2. Edit the service; the route is almost never what you want to change.
3. Add/modify tests in `apps/api/tests/`.

### Add a scheduled job

1. Add a cycle function (`_run_<name>_cycle`) in [`background_scheduler.py`](../../apps/api/app/services/background_scheduler.py).
2. Add a loop function and start it in `scheduled_loop_startup()`; it is invoked from the FastAPI `lifespan` in [`main.py`](../../apps/api/app/main.py).
3. Keep the tick at 60s — share with existing loops rather than spinning new ones.

---

## Frontend

### Change a dashboard page

1. Page file: `apps/web/app/dashboard/<domain>/page.tsx`.
2. Data hook: `apps/web/lib/<domain>.ts`. If it's missing an endpoint, add a function there rather than fetching inline.
3. UI components: `apps/web/components/<domain>/` (or reuse `components/ui/` shadcn primitives).
4. Tests: `apps/web/app/dashboard/<domain>/__tests__/*.test.tsx`.
5. Run `cd apps/web && npm test`.

### Change widget data / add a chart

1. Widget dispatch lives in [`components/dashboard/widget-renderer.tsx`](../../apps/web/components/dashboard/widget-renderer.tsx).
2. Data normalization lives in [`components/dashboard/widget-data-adapter.ts`](../../apps/web/components/dashboard/widget-data-adapter.ts).
3. For a new chart type: add `components/dashboard/charts/<type>.tsx` (pure SVG — no chart libs), then a branch in the renderer + adapter.
4. Tests: [`components/dashboard/__tests__/charts.test.tsx`](../../apps/web/components/dashboard/__tests__/charts.test.tsx), `widget-renderer.test.tsx`, `widget-data-adapter.test.ts`.

### Add a new lib client

1. `apps/web/lib/<domain>.ts`.
2. Import the shared `api` from `lib/api.ts` — never fetch directly.
3. Export typed functions; keep interfaces in the same file unless reused.
4. Add a focused unit test in `apps/web/lib/__tests__/<domain>.test.ts`.

### Subscribe a page to live updates

1. Use the `useStream` hook from [`apps/web/lib/stream.ts`](../../apps/web/lib/stream.ts).
2. The backend must emit events via `event_service` → `stream_service`; streaming route is `/api/v1/streaming/...` ([`routes/streaming.py`](../../apps/api/app/api/routes/streaming.py)).

---

## Integrations

### Add a new connector (outbound channel)

1. Model: extend or add to [`models/connector.py`](../../apps/api/app/models/connector.py) if a new type.
2. Dispatch branch: [`webhook_connector_service.dispatch_webhook`](../../apps/api/app/services/webhook_connector_service.py).
3. Notification routing: add a channel case in [`notification_delivery_service.py`](../../apps/api/app/services/notification_delivery_service.py).
4. UI: `apps/web/app/dashboard/connectors/` + `lib/connectors.ts`.
5. Credentials: store via [`credential_vault_service`](../../apps/api/app/services/credential_vault_service.py).

### Change GitHub webhook handling

1. Signature + envelope: [`services/webhook_service.py`](../../apps/api/app/services/webhook_service.py).
2. Per-event handler: `process_pr_event` · `process_workflow_run_event` · `process_issues_event` · `process_push_event` · `process_release_event` · `process_check_run_event` — all in the same file.
3. Related services: `pr_service`, `ci_pipeline_service`, `issue_sync_service`, `code_ops_service`, `release_gate_service`.
4. Route: [`routes/github_integration.py`](../../apps/api/app/api/routes/github_integration.py).

### Add an API key scope

1. Define the scope value in [`api_key_service.py`](../../apps/api/app/services/api_key_service.py).
2. Gate routes via `Depends(require_scope("<scope>"))` from [`core/authz_deps.py`](../../apps/api/app/core/authz_deps.py).
3. Migration if persisted as an enum.

---

## SDKs

### Add a new method to the SDKs

1. Ship the backend route first.
2. Update [`apps/api/app/sdk/python_client.py`](../../apps/api/app/sdk/python_client.py) — add method to the relevant resource client.
3. Update [`apps/api/app/sdk/typescript_client.ts`](../../apps/api/app/sdk/typescript_client.ts) — mirror the method.
4. Optionally regenerate from `/openapi.json` via [`openapi-generator-config.yaml`](../../apps/api/app/sdk/openapi-generator-config.yaml).
5. Bump version in `apps/api/app/sdk/pyproject.toml` + `package.json`.

---

## Tests

| Want to test… | Where |
| :-- | :-- |
| A route | `apps/api/tests/test_<domain>.py` — use `client` + `session` fixtures |
| A service | `apps/api/tests/test_<service>.py` — call the service directly with `session` |
| A page | `apps/web/app/dashboard/<domain>/__tests__/*.test.tsx` |
| A component | `apps/web/components/<area>/__tests__/*.test.tsx` |
| A lib client | `apps/web/lib/__tests__/<domain>.test.ts` |
| The CLI | `apps/local/tests/test_*.py` |

> Backend tests use **aiosqlite**, not Postgres. Don't add tests that rely on Postgres-only features without gating.

---

## Docs

| Change kind | File to update |
| :-- | :-- |
| New subsystem or breaking architectural change | [`docs/ARCHITECTURE.md`](../ARCHITECTURE.md) |
| Milestone / wave closure | [`docs/MILESTONE_SUMMARY.md`](../MILESTONE_SUMMARY.md) + [`docs/agent-handoffs/`](../agent-handoffs/) |
| Dev / run / test procedure change | [`docs/DEVELOPMENT_WORKFLOW.md`](../DEVELOPMENT_WORKFLOW.md) |
| New route group the public cares about | [`docs/api-ecosystem.md`](../api-ecosystem.md) |
| Dashboard / analytics change | [`docs/analytics-portfolio.md`](../analytics-portfolio.md) |
| Code-intelligence change | [`docs/code-intelligence.md`](../code-intelligence.md) |
| New mental model that agents must know | This folder ([`docs/project-memory/`](./README.md)) |

---

## Migrations & models

### Add a model

1. `apps/api/app/models/<name>.py` — SQLAlchemy 2 declarative, inherits the shared `Base`.
2. Import it in `apps/api/app/models/__init__.py` so it's registered.
3. Generate a migration: `alembic revision --autogenerate -m "<name>"` (run from `apps/api/`).
4. Inspect the generated file — hand-edit enum / index / default issues.
5. `alembic upgrade head` locally.
6. Tests bypass Alembic (they use `create_all`), so migration issues only surface at real-Postgres boot. Smoke-test with `docker compose up -d` once.

### Known migration quirk

`0022_add_architecture_tables` raises `DuplicateObjectError` for `arch_node_type` enum on a fresh Postgres. Workaround documented in [`docs/DEVELOPMENT_WORKFLOW.md`](../DEVELOPMENT_WORKFLOW.md).

---

## Config / env vars

- All settings: [`apps/api/app/core/config.py`](../../apps/api/app/core/config.py) (`Settings` via pydantic-settings).
- Canonical env template: [`.env.example`](../../.env.example).
- Frontend env: `apps/web/.env*` — `NEXT_PUBLIC_API_BASE_URL` is the main knob.

---

## CI / tooling

- Pipeline: [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml) — 3 jobs.

| Job | Steps |
| :-- | :-- |
| backend | `ruff check` → `ruff format --check` → `pytest` |
| frontend | `tsc --noEmit` → `eslint` → `vitest run --coverage` → `next build` |
| local-cli | `pytest` in `apps/local/` |

- Lint / format: `ruff` (Python), `eslint` + `prettier` (TS).
- Type check: `mypy`-style strictness via Pydantic v2 + SQLAlchemy 2 annotations; `tsc --noEmit` for the frontend.
