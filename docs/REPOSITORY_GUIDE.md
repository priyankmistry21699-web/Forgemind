# ForgeMind — Repository Guide

> A navigation map for the ForgeMind monorepo. Answers the question **"I want to change X — where do I start?"** for the most common contributions. Pair with [ARCHITECTURE.md](ARCHITECTURE.md) for the design reference and [DEVELOPMENT_WORKFLOW.md](DEVELOPMENT_WORKFLOW.md) for how to run / test / migrate.

---

## Top-level layout

```
apps/
  api/            FastAPI backend — routes, services, models, migrations, SDK
  web/            Next.js 15 frontend — app router, lib API clients, tests
  worker/         Async agent worker loop (architect / coder / reviewer / tester)
  local/          `forgemind` standalone CLI (FM-091 → FM-100)
packages/
  agents/ connectors/ core/ orchestrator/ schemas/ security/ utils/ verification/
docs/             Architecture + milestone history + topical guides (this folder)
scripts/          Operational helpers (seed data, smoke scripts, demos)
deployment/       Docker images, compose overlays, reverse-proxy templates
.github/          CI (3 jobs) + issue/PR templates
```

Counts at HEAD `2a4e8fc`: **51** API routers · **103** services · **44** models · **25** dashboard route folders · **34** frontend `lib/` modules · **1559 / 231 / 61** tests across backend / frontend / local CLI.

---

## "I want to add a …"

### … REST endpoint

1. **Pick a router file** under [`apps/api/app/api/routes/`](../apps/api/app/api/routes/). One file per feature area (e.g. `projects.py`, `runs.py`, `analytics.py`). Create a new one if the feature truly has no home.
2. **Define the Pydantic schemas** in [`apps/api/app/schemas/`](../apps/api/app/schemas/). Keep request and response schemas separate.
3. **Implement business logic in a service** under [`apps/api/app/services/`](../apps/api/app/services/) — routes must stay thin.
4. **Wire the router** in [`apps/api/app/main.py`](../apps/api/app/main.py) (public) or [`apps/api/app/api/router.py`](../apps/api/app/api/router.py) (`/api/v1/…` versioned surface).
5. **Add dependencies** (`get_current_user`, scope checks, rate limit) from [`apps/api/app/core/auth.py`](../apps/api/app/core/auth.py) and [`apps/api/app/core/authz_deps.py`](../apps/api/app/core/authz_deps.py).
6. **Write tests** under [`apps/api/tests/`](../apps/api/tests/) using the `client` and `session` fixtures from `conftest.py`.
7. **Update the OpenAPI spec** by running the API — it is generated from the FastAPI app. If you expose a public `/api/v1/` endpoint, also verify the SDK regenerates cleanly (`openapi-generator-config.yaml` under [`apps/api/app/sdk/`](../apps/api/app/sdk/)).

### … database model

1. **Create the model** under [`apps/api/app/models/`](../apps/api/app/models/), inheriting `Base`.
2. **Register it** by importing from [`apps/api/app/db/base.py`](../apps/api/app/db/base.py) — autogenerate will miss it otherwise.
3. **Generate the migration**: `cd apps/api && alembic revision --autogenerate -m "add foo"`.
4. **Inspect the migration file** in [`apps/api/alembic/versions/`](../apps/api/alembic/versions/). Hand-edit enum creation, defaults, and server defaults. Confirm `down_revision` points at the current head (`alembic heads`).
5. **Upgrade locally**: `alembic upgrade head`.
6. **Add a Pydantic schema** mirroring the model under [`apps/api/app/schemas/`](../apps/api/app/schemas/) (do not leak ORM objects out of services).
7. **Add tests** that exercise the CRUD path through a service.

### … service / business logic

1. Create the module under [`apps/api/app/services/`](../apps/api/app/services/).
2. Accept `session: AsyncSession` (SQLAlchemy 2 async) plus domain inputs. Return plain dataclasses / dicts / Pydantic models — never raw ORM instances to routes.
3. Import existing services rather than duplicating — [`adaptive_orchestrator`](../apps/api/app/services/adaptive_orchestrator.py), [`execution_service`](../apps/api/app/services/execution_service.py), [`execution_health_service`](../apps/api/app/services/execution_health_service.py), [`event_service`](../apps/api/app/services/event_service.py), and [`audit_log_service`](../apps/api/app/services/audit_log_service.py) are used everywhere.
4. Test it directly via the `session` fixture in [`apps/api/tests/conftest.py`](../apps/api/tests/conftest.py).

### … dashboard page

1. Create a folder under [`apps/web/app/dashboard/`](../apps/web/app/dashboard/) — the folder name is the URL segment. Add a `page.tsx` and optional `loading.tsx` / `error.tsx`.
2. Use a typed API client from [`apps/web/lib/`](../apps/web/lib/) (one file per feature area — `api.ts`, `projects.ts`, `approvals.ts`, `analytics.ts`, etc.). If none fits, add a new one following the existing shape.
3. Compose UI with Tailwind utility classes + shadcn primitives from [`apps/web/components/ui/`](../apps/web/components/ui/).
4. If the page needs live updates, subscribe via the SSE helpers in [`apps/web/lib/stream.ts`](../apps/web/lib/stream.ts) / [`apps/web/lib/hooks/use-stream.ts`](../apps/web/lib/hooks/use-stream.ts).
5. Add Vitest tests under [`apps/web/__tests__/`](../apps/web/__tests__/) using `@testing-library/react` — mirror the structure of existing tests (e.g. `dashboard-home.test.tsx`, `projects-page.test.tsx`).
6. Run `npm run lint && npx tsc --noEmit && npm test && npm run build`.

### … frontend API client

1. Add a file under [`apps/web/lib/`](../apps/web/lib/) named after the feature area (`foo.ts`). Export typed functions that call the backend via the shared `apiClient` in [`apps/web/lib/api.ts`](../apps/web/lib/api.ts).
2. Export explicit types for every request and response — keep them co-located, do not import from backend.
3. Add a Vitest test under [`apps/web/__tests__/lib/`](../apps/web/__tests__/) mocking `fetch` (see `lib-api.test.ts`, `lib-projects.test.ts` for the canonical patterns).

### … agent

1. Add the agent class under [`apps/worker/worker/agents/`](../apps/worker/worker/agents/), inheriting [`base.py`](../apps/worker/worker/agents/base.py).
2. Register it in [`apps/worker/worker/agents/registry.py`](../apps/worker/worker/agents/registry.py) so the composition engine can dispatch to it.
3. If it needs new adaptive behaviour, extend [`apps/api/app/services/composition_service.py`](../apps/api/app/services/composition_service.py).
4. Phase profiles live in [`apps/api/app/services/phase_agent_profile_service.py`](../apps/api/app/services/phase_agent_profile_service.py) — add a profile mapping if the agent should run in a specific phase.
5. Worker tests under `apps/worker/tests/` — mirror existing agent test files.

### … LLM call

1. Use [`apps/api/app/core/llm.py`](../apps/api/app/core/llm.py) — it wraps LiteLLM with normalization, schema validation, and retry.
2. Pick the model from env (`PLANNER_MODEL` for planner, agent-specific env elsewhere). Never hardcode model names in services.
3. Always pass a structured output schema or a strict prompt template — every LLM call the planner / agents make is schema-validated.

### … webhook / integration (Wave 16)

1. Outbound webhook endpoints are stored as `WebhookEndpoint` in [`apps/api/app/models/api_ecosystem.py`](../apps/api/app/models/api_ecosystem.py) and delivered by [`webhook_service`](../apps/api/app/services/webhook_service.py) with HMAC-signed bodies.
2. Register or manage endpoints through [`apps/api/app/api/routes/api_ecosystem.py`](../apps/api/app/api/routes/api_ecosystem.py).
3. For connector-side integrations (Slack / email / PagerDuty / generic HTTP), use [`webhook_connector_service`](../apps/api/app/services/webhook_connector_service.py) and the connector packages under [`packages/connectors/`](../packages/connectors/).
4. See [api-ecosystem.md](api-ecosystem.md) for the full surface (API-key auth, rate tiers, SDK regeneration).

### … CLI command

1. Add the module under [`apps/local/forgemind_local/`](../apps/local/forgemind_local/). Each existing command is its own file (e.g. `local_chat.py`, `local_exec.py`, `local_patch.py`, `local_pr.py`, `ide_integration.py`, `local_handoff.py`, `local_state.py`).
2. Register it in the Typer app in [`apps/local/forgemind_local/cli.py`](../apps/local/forgemind_local/cli.py).
3. Reuse the config + repo index + state helpers under [`apps/local/forgemind_local/core/`](../apps/local/forgemind_local/core/) — don't duplicate file-walking or config parsing.
4. Add tests under [`apps/local/tests/`](../apps/local/tests/) — the 61-test suite uses pytest + `typer.testing.CliRunner`.
5. Run `cd apps/local && pytest && ruff check .`.

### … enterprise governance policy

1. Policy rules are evaluated by [`governance_engine_service`](../apps/api/app/services/governance_engine_service.py).
2. Storage lives in [`apps/api/app/models/enterprise_governance.py`](../apps/api/app/models/enterprise_governance.py).
3. Surface is [`apps/api/app/api/routes/enterprise_governance.py`](../apps/api/app/api/routes/enterprise_governance.py) — extend the DSL there.
4. Release gates (FM-177) are enforced in [`release_gate_service`](../apps/api/app/services/release_gate_service.py).

### … analytics metric

1. The auto-capture hook is in [`execution_health_service`](../apps/api/app/services/execution_health_service.py) — emit a metric from the lifecycle event where the data is available (never at the route layer).
2. Widget chart types live in [`apps/web/components/dashboard/`](../apps/web/components/dashboard/) — pure SVG, no chart library.
3. See [analytics-portfolio.md](analytics-portfolio.md) for the full Wave 15 surface (budgets, alerts, portfolio, executive summary).

### … code-intelligence feature (pattern rule, debt score, etc.)

1. See [code-intelligence.md](code-intelligence.md) for the authoritative guide.
2. Pattern rule engine: [`pattern_debt_service`](../apps/api/app/services/pattern_debt_service.py).
3. Dependency graph: [`code_graph_service`](../apps/api/app/services/code_graph_service.py).
4. Flakiness / complexity: [`flakiness_complexity_service`](../apps/api/app/services/flakiness_complexity_service.py).

---

## Key cross-cutting modules

Knowing these saves time — they are imported everywhere.

| Concern | Module |
| ------- | ------ |
| DB session + engine | [`apps/api/app/db/session.py`](../apps/api/app/db/session.py) |
| Base model + metadata | [`apps/api/app/db/base.py`](../apps/api/app/db/base.py) |
| App factory + middleware | [`apps/api/app/main.py`](../apps/api/app/main.py) |
| Versioned router `/api/v1/` | [`apps/api/app/api/router.py`](../apps/api/app/api/router.py) |
| Auth dependencies | [`apps/api/app/core/auth.py`](../apps/api/app/core/auth.py) |
| Authorization (scopes / RBAC) | [`apps/api/app/core/authz_deps.py`](../apps/api/app/core/authz_deps.py) |
| Settings (env via pydantic-settings) | [`apps/api/app/core/config.py`](../apps/api/app/core/config.py) |
| LLM wrapper | [`apps/api/app/core/llm.py`](../apps/api/app/core/llm.py) |
| Orchestration entrypoint | [`apps/api/app/services/adaptive_orchestrator.py`](../apps/api/app/services/adaptive_orchestrator.py) |
| Execution driver | [`apps/api/app/services/execution_service.py`](../apps/api/app/services/execution_service.py) |
| Event log writer | [`apps/api/app/services/event_service.py`](../apps/api/app/services/event_service.py) |
| Audit writer | [`apps/api/app/services/audit_log_service.py`](../apps/api/app/services/audit_log_service.py) |
| SSE broadcaster | [`apps/api/app/services/stream_service.py`](../apps/api/app/services/stream_service.py) |
| Metrics (Prometheus) | [`apps/api/app/core/metrics.py`](../apps/api/app/core/metrics.py) |
| Rate limiter | [`apps/api/app/core/rate_limit.py`](../apps/api/app/core/rate_limit.py) |
| Shared API client (FE) | [`apps/web/lib/api.ts`](../apps/web/lib/api.ts) |
| SSE hook (FE) | [`apps/web/lib/hooks/use-stream.ts`](../apps/web/lib/hooks/use-stream.ts) |
| Dashboard shell (FE) | [`apps/web/app/dashboard/layout.tsx`](../apps/web/app/dashboard/layout.tsx) |

---

## Tests live next to the code they cover

| Surface | Location | Fixtures |
| ------- | -------- | -------- |
| Backend | [`apps/api/tests/`](../apps/api/tests/) | [`conftest.py`](../apps/api/tests/conftest.py) provides `client` + `session` against aiosqlite |
| Frontend | [`apps/web/__tests__/`](../apps/web/__tests__/) | Vitest + Testing Library; config in [`apps/web/vitest.config.ts`](../apps/web/vitest.config.ts) |
| Worker | `apps/worker/tests/` | pytest |
| Local CLI | `apps/local/tests/` | pytest + `typer.testing.CliRunner` |

A test file name usually mirrors its target: `test_projects.py` covers `routes/projects.py`; `projects-page.test.tsx` covers `app/dashboard/projects/page.tsx`. Keep that convention.

---

## Documentation map

| Audience | Start here |
| -------- | ---------- |
| "What does ForgeMind do?" | [../README.md](../README.md) |
| "How is it built?" | [ARCHITECTURE.md](ARCHITECTURE.md) |
| "How do I run / test / migrate it?" | [DEVELOPMENT_WORKFLOW.md](DEVELOPMENT_WORKFLOW.md) |
| "What shipped and when?" | [MILESTONE_SUMMARY.md](MILESTONE_SUMMARY.md) |
| "How does Wave 14 (code intelligence) work?" | [code-intelligence.md](code-intelligence.md) |
| "How does Wave 15 (analytics / portfolio) work?" | [analytics-portfolio.md](analytics-portfolio.md) |
| "How does Wave 16 (API / webhooks / ecosystem) work?" | [api-ecosystem.md](api-ecosystem.md) |
| "How do I deploy?" | [DEPLOYMENT.md](DEPLOYMENT.md) |
| "What debt exists?" | [TECHNICAL_DEBT.md](TECHNICAL_DEBT.md) |
| Per-milestone delivery notes | [agent-handoffs/](agent-handoffs/) |

---

## House rules

- Routes stay thin; business logic goes in services.
- Services never return raw ORM instances to routes.
- No `print()` — use the configured logger.
- Always include a request scope + auth check for `/api/v1/` endpoints (webhooks and `/health`/`/metrics` are the only public-by-design routes).
- Every new backend test uses the provided `session` fixture against aiosqlite (see `conftest.py`) — do not spin up real Postgres in tests.
- Every new frontend test uses `@testing-library/react` and Vitest's `vi.mock` — do not hit the real backend.
- Every new migration chains from `alembic heads` — never `down_revision=None` on a non-root revision.
- Run ruff + ESLint + tsc + pytest + Vitest before opening a PR.
