# 2 · Repo Map

```
Forgemind/
├── apps/
│   ├── api/            FastAPI backend  (routes · services · models · migrations · SDK)
│   ├── web/            Next.js 15 frontend
│   ├── worker/         Async agent loop (architect · coder · reviewer · tester)
│   ├── local/          forgemind standalone CLI
│   └── local-agent/    (legacy / WIP — not a primary surface)
├── packages/
│   ├── agents/         shared (README only — agent loop lives in apps/worker)
│   ├── connectors/     shared (README only — connector logic lives in apps/api)
│   ├── core/           shared core utilities
│   ├── orchestrator/   shared orchestrator primitives
│   ├── schemas/        shared TS types
│   ├── security/       shared security helpers
│   ├── utils/          shared utils
│   └── verification/   shared verification helpers
├── docs/
│   ├── ARCHITECTURE.md · MILESTONE_SUMMARY.md · REPOSITORY_GUIDE.md
│   ├── DEVELOPMENT_WORKFLOW.md · DEPLOYMENT.md · TECHNICAL_DEBT.md
│   ├── api-ecosystem.md · analytics-portfolio.md · code-intelligence.md
│   ├── agent-handoffs/          one handoff per milestone wave
│   ├── assets/                  brand assets (logo + mark SVGs)
│   └── project-memory/          THIS FOLDER
├── scripts/                     operator exercise + data helpers
├── deploy/                      Docker images + reverse-proxy templates
├── .github/workflows/ci.yml     3-job CI (backend · frontend · local-cli)
├── docker-compose.yml · docker-compose.prod.yml
├── Makefile
└── FORGEMIND_*ROADMAP*.md       product plans (V1 → V5)
```

## High-signal entry points

| Want to… | Open this first |
| :-- | :-- |
| Understand how the API boots | [apps/api/app/main.py](../../apps/api/app/main.py) — `lifespan()`, middleware stack, `app.include_router(api_router)` |
| Find a route | [apps/api/app/api/routes/](../../apps/api/app/api/routes/) — one file per domain, registered in [routes/__init__.py](../../apps/api/app/api/routes/__init__.py) |
| Understand the agent loop | [apps/worker/worker/main.py](../../apps/worker/worker/main.py) → [apps/worker/worker/agents/](../../apps/worker/worker/agents/) |
| See every scheduled job | [apps/api/app/services/background_scheduler.py](../../apps/api/app/services/background_scheduler.py) (`escalation_loop`, `retention_loop`, `scheduled_report_loop`) |
| See the public API surface | [apps/api/app/api/routes/](../../apps/api/app/api/routes/) + [apps/api/app/sdk/](../../apps/api/app/sdk/) |
| Understand frontend routing | [apps/web/app/dashboard/](../../apps/web/app/dashboard/) — 25 domain folders |
| Understand frontend data layer | [apps/web/lib/](../../apps/web/lib/) — 33 modules, one typed client per backend domain + [api.ts](../../apps/web/lib/api.ts) shared HTTP |
| Understand how SSE streams work | [apps/web/lib/stream.ts](../../apps/web/lib/stream.ts) + backend [stream_service.py](../../apps/api/app/services/stream_service.py) + [routes/streaming.py](../../apps/api/app/api/routes/streaming.py) |
| Trace a CI test failure | [.github/workflows/ci.yml](../../.github/workflows/ci.yml) — 3 jobs: backend (ruff + pytest), frontend (tsc + eslint + vitest + next build), local-cli (pytest) |
| Wire a new SDK method | [apps/api/app/sdk/python_client.py](../../apps/api/app/sdk/python_client.py) · [apps/api/app/sdk/typescript_client.ts](../../apps/api/app/sdk/typescript_client.ts) · regen config [openapi-generator-config.yaml](../../apps/api/app/sdk/openapi-generator-config.yaml) |

## Where the logic lives (rule of thumb)

- **Business logic → services.** Routes stay thin, services are fat.
- **DB access → services only.** No ORM queries in routes, no raw SQL in routes or components.
- **LLM calls → via [core/llm.py](../../apps/api/app/core/llm.py).** Cost recording happens there.
- **Types at boundaries → Pydantic v2 schemas** ([apps/api/app/schemas/](../../apps/api/app/schemas/)).
- **Frontend does no business logic.** Pages call `lib/<domain>.ts` which calls `/api/v1/...`.

## Backend directory breakdown

| Path | Role |
| :-- | :-- |
| `apps/api/app/api/routes/` | 53 route modules — thin, validate + authorize + call service |
| `apps/api/app/services/` | 109 services — all business logic, DB access, LLM calls |
| `apps/api/app/models/` | 42 SQLAlchemy models (async, `AsyncAttrs` + `DeclarativeBase`) |
| `apps/api/app/schemas/` | 38 Pydantic v2 schemas — request/response DTOs |
| `apps/api/app/core/` | auth · authz · config · llm · rate limit · middleware · metrics |
| `apps/api/app/db/` | session factory, Base, engine |
| `apps/api/app/sdk/` | Python + TypeScript SDK sources + OpenAPI generator config |
| `apps/api/alembic/` | migrations (head: `fm161_170_search_knowledge`) |
| `apps/api/tests/` | pytest suite (1559 tests, aiosqlite-backed) |

## Frontend directory breakdown

| Path | Role |
| :-- | :-- |
| `apps/web/app/dashboard/` | 25 App Router route folders — one per domain |
| `apps/web/app/login/` | auth page |
| `apps/web/lib/` | 33 typed API clients + `api.ts` (shared HTTP) + `stream.ts` (SSE) + `auth-context.tsx` |
| `apps/web/components/` | `ui/` (shadcn primitives) · `layout/` · domain widgets (approvals, artifacts, chat, dashboard, events, planner, projects, tasks) |
| `apps/web/components/dashboard/` | `dashboard-grid.tsx` · `widget-renderer.tsx` · `widget-data-adapter.ts` · `charts/` (pure SVG) |

## Tests map

| Surface | Location | Count |
| :-- | :-- | --: |
| Backend pytest | `apps/api/tests/` | 1559 |
| Frontend Vitest | `apps/web/**/__tests__/` | 231 / 37 files |
| Local CLI pytest | `apps/local/tests/` | 61 |
