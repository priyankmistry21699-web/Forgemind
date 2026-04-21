# ForgeMind — Development Workflow

> A practical guide for running, testing, linting, migrating, and contributing to ForgeMind locally. Use this alongside [REPOSITORY_GUIDE.md](REPOSITORY_GUIDE.md) (where-to-start map) and [ARCHITECTURE.md](ARCHITECTURE.md) (system design).

---

## 1. Prerequisites

| Tool | Version | Why |
| ---- | ------- | --- |
| Docker + Docker Compose | Latest | Postgres 16, Redis 7, MinIO, and optional API/web containers |
| Python | 3.12+ | Backend, worker, local CLI |
| Node.js | 20+ | Frontend (Next.js 15) |
| Git | Latest | — |
| (optional) ruff | bundled via `pip install -e apps/api[dev]` | Backend lint + format |
| (optional) `make` | — | Convenience targets |

An LLM credential is **optional** — the planner and agents fall back to structured stubs if no API key is configured. For realistic runs, set one of `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, or `GOOGLE_API_KEY` in `.env`.

---

## 2. Boot options

### 2.1 Full Docker Compose (recommended for first boot)

```bash
cp .env.example .env
# set at least one LLM key inside .env if you want real LLM calls
docker compose up -d
docker compose exec api alembic upgrade head
```

Services:

- Frontend: http://localhost:3000
- API docs: http://localhost:8000/docs (Swagger) · /redoc (ReDoc) · /openapi.json (spec)
- MinIO console: http://localhost:9001
- Postgres on 5432, Redis on 6379

### 2.2 Hybrid (infra in Docker, app processes on host)

This is the daily-dev pattern — fastest iteration because code reloads without container rebuilds.

```powershell
docker compose up -d postgres redis minio

# Terminal 1 — backend
cd apps/api
pip install -e ".[dev]"
alembic upgrade head           # or see §5 for bootstrap workaround
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 — worker
cd apps/worker
python -m worker.main

# Terminal 3 — frontend
cd apps/web
npm install
npm run dev
```

### 2.3 `make` shortcuts

```bash
make install        # install everything
make dev            # API + web + infra
make dev-worker     # worker only
make migrate        # alembic upgrade head
make test           # all test suites
make lint           # ruff + eslint
make format         # ruff format + prettier
```

### 2.4 Local CLI only (no server)

```bash
pip install -e apps/local
cd <some-git-repo>
forgemind init
forgemind attach
forgemind ask "where does X live?"
```

---

## 3. Environment variables

Canonical list lives in [`.env.example`](../.env.example). Most-used:

| Variable | Default | Purpose |
| -------- | ------- | ------- |
| `APP_ENV` | `development` | environment mode |
| `SECRET_KEY` | `change-me-...` | JWT + session signing (required in prod) |
| `POSTGRES_HOST` / `PORT` / `DB` / `USER` / `PASSWORD` | local defaults | primary datastore |
| `REDIS_HOST` / `PORT` | `localhost` / `6379` | cache + queue |
| `MINIO_ENDPOINT` / `ACCESS_KEY` / `SECRET_KEY` | local defaults | object storage |
| `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` / `GOOGLE_API_KEY` | — | LLM — any one enables real planning/execution |
| `PLANNER_MODEL` | `gpt-4o` | model used by planner |
| `WORKER_POLL_INTERVAL` | `5` | seconds between worker polls |
| `WORKER_MAX_TASKS_PER_CYCLE` | `3` | worker concurrency |
| `CORS_ORIGINS` | `http://localhost:3000` | comma-separated allowlist |

---

## 4. Testing

| Suite | Command | Current count (HEAD `2a4e8fc`) |
| ----- | ------- | ------------------------------ |
| Backend pytest | `cd apps/api && pytest` | **1559 / 1559** |
| Backend pytest (single file) | `pytest tests/test_projects.py -q` | — |
| Backend pytest (one test) | `pytest tests/test_projects.py::test_create -q` | — |
| Frontend Vitest | `cd apps/web && npm test` | **231 / 231** across 37 files |
| Frontend coverage (v8) | `cd apps/web && npm run test:coverage` | stmts 51.00 / branches 55.57 / funcs 55.48 / lines 51.73 |
| Local CLI pytest | `cd apps/local && pytest` | **61 / 61** |

Backend tests use **aiosqlite in-memory** and `Base.metadata.create_all()` in `tests/conftest.py`. They **do not** run Alembic. This is intentional (fast isolated tests) and is why the CI stayed green through the multi-head alembic break fixed in `2a4e8fc` — that breakage only manifested against a real Postgres.

---

## 5. Migrations

Alembic chain lives in [`apps/api/alembic/versions/`](../apps/api/alembic/versions/). Head revision: `fm161_170_search_knowledge`.

### 5.1 Creating a migration

```bash
cd apps/api
alembic revision --autogenerate -m "add foo table"
# inspect the generated file carefully — hand-edit if needed
alembic upgrade head
```

Rules:

1. Every new revision's `down_revision` must be set from `alembic heads` (never `None` — that breaks the chain).
2. Import any new model in [`apps/api/app/db/base.py`](../apps/api/app/db/base.py) **before** running `autogenerate`, otherwise autogenerate will not see it.
3. Run the full backend test suite before committing (`pytest`).

### 5.2 Known quirk: migration `0022_add_architecture_tables`

Against a fresh Postgres, migration `2026_04_03_0022_add_architecture_tables.py` raises `DuplicateObjectError` for the `arch_node_type` enum. Tests never hit it (they bypass Alembic entirely) so CI stayed green. The local-runtime workaround:

```bash
cd apps/api
# Create schema directly from models
python _bootstrap_schema.py
# Mark Alembic as up-to-date at heads so future revisions chain cleanly
alembic stamp heads
```

[`apps/api/_bootstrap_schema.py`](../apps/api/_bootstrap_schema.py) is a small helper that runs `Base.metadata.create_all()` against the configured `DATABASE_URL`. It is intentionally uncommitted / working-tree-only (it is a dev workaround, not a production path). Production must use proper Alembic upgrade — fix migration 0022 before promoting.

### 5.3 Dev user workaround

If a fresh database throws `projects_owner_id_fkey` violations when creating a project, seed the dev-mode stub user:

```bash
docker exec forgemind-postgres psql -U forgemind -d forgemind \
  -c "INSERT INTO users (id, email, display_name, is_active) VALUES ('00000000-0000-0000-0000-000000000001', 'dev@forgemind.dev', 'Dev User', true) ON CONFLICT (id) DO NOTHING;"
```

The dev auth stub uses that UUID as the owner of requests when no JWT is present.

---

## 6. Lint, format, typecheck, build

| Surface | Command | Expected |
| ------- | ------- | -------- |
| Backend lint | `cd apps/api && ruff check .` | 0 errors |
| Backend format | `cd apps/api && ruff format --check .` | clean |
| Frontend lint | `cd apps/web && npm run lint` | clean (ESLint flat config) |
| Frontend typecheck | `cd apps/web && npx tsc --noEmit` | clean |
| Frontend build | `cd apps/web && npm run build` | clean |
| Local CLI lint | `cd apps/local && ruff check .` | 0 errors |

Run these before opening a PR — CI runs the same set and blocks on any regression.

---

## 7. CI pipeline

[`.github/workflows/ci.yml`](../.github/workflows/ci.yml) runs three jobs on every push and PR:

| Job | Steps |
| --- | ----- |
| **backend** | `ruff check .` → `ruff format --check .` → `pytest` against `apps/api` |
| **frontend** | `npm ci` → `tsc --noEmit` → `npm run lint` → `npm run test:coverage` → `npm run build`; uploads coverage artifact |
| **local-cli** | `pip install -e apps/local[dev]` → `pytest` against `apps/local` |

All three must be green on `main`. If you introduce a format-only or lint-only change, prefer a dedicated commit so it is easy to revert.

---

## 8. Branching & commits

- Work off `main`; branch names free-form.
- Keep commits focused (one logical change per commit). Follow the `type(scope): summary` convention loosely — examples in git history: `fix(api): chain fm161_170 migration to 0026`, `test(fe): restore FM-035 operator polish`.
- Include a `-m "body"` describing **why** the change exists when the subject line is not enough.
- Run `pytest`, `ruff check`, and `ruff format --check` locally before committing backend changes. Run `npm run lint`, `npx tsc --noEmit`, and `npm test` before committing frontend changes.
- Never `--force-push` to `main`.

---

## 9. Smoke-testing a local stack

After booting:

```powershell
# health
Invoke-WebRequest http://127.0.0.1:8000/health -UseBasicParsing

# create a project
$body = '{"name":"Smoke","description":"smoke","prompt":"Build X"}'
Invoke-WebRequest -Uri http://127.0.0.1:8000/api/v1/projects `
  -Method POST -Body $body -ContentType "application/json" -UseBasicParsing

# list projects
Invoke-WebRequest http://127.0.0.1:8000/api/v1/projects -UseBasicParsing

# dashboard
Invoke-WebRequest http://localhost:3000/dashboard -UseBasicParsing
```

For a scripted end-to-end exercise against an in-process aiosqlite app (no real Postgres required), see [`scripts/operator_exercise.py`](../scripts/operator_exercise.py).

---

## 10. Observability while developing

- **Metrics:** `GET http://localhost:8000/metrics` (Prometheus format).
- **Request IDs:** every response carries `X-Request-ID`; the value appears in backend logs.
- **SSE streams:** `GET /runs/{id}/stream` and `/stream/events` for dashboards; browser DevTools shows the connection.
- **Worker logs:** the worker process logs its poll cycle, claimed tasks, and agent dispatch.

---

## 11. Where to read more

- [REPOSITORY_GUIDE.md](REPOSITORY_GUIDE.md) — where to add code for a given kind of change.
- [ARCHITECTURE.md](ARCHITECTURE.md) — full design reference.
- [MILESTONE_SUMMARY.md](MILESTONE_SUMMARY.md) — wave-by-wave feature delivery.
- [code-intelligence.md](code-intelligence.md), [analytics-portfolio.md](analytics-portfolio.md), [api-ecosystem.md](api-ecosystem.md) — topical developer guides.
- [TECHNICAL_DEBT.md](TECHNICAL_DEBT.md) — known debt items.
