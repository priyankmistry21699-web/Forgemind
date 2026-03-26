# ForgeMind API

> FastAPI backend for the ForgeMind platform.

## Overview

This is the main API server that handles:

- User authentication (via Clerk JWTs) — _planned_
- Project and task management (CRUD) — _planned_
- Agent orchestration triggers — _planned_
- Connector management and token vault — _planned_
- WebSocket connections for real-time updates — _planned_
- Artifact storage and retrieval — _planned_

## Project Structure

```
apps/api/
├── pyproject.toml              # Dependencies and project metadata
├── alembic.ini                 # Alembic configuration
├── alembic/
│   ├── env.py                  # Async migration environment
│   ├── script.py.mako          # Migration file template
│   └── versions/               # Auto-generated migration files
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app factory + entrypoint
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py           # Settings (loaded from env vars)
│   │   └── auth_stub.py        # Temporary auth dependency (→ Clerk in FM-011)
│   ├── models/
│   │   ├── __init__.py         # Re-exports all models
│   │   ├── user.py             # User model
│   │   ├── project.py          # Project model
│   │   ├── run.py              # Run model
│   │   └── task.py             # Task model (with DAG dependencies)
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── project.py          # Project Pydantic schemas
│   │   ├── prompt_intake.py    # Prompt intake schemas
│   │   └── task.py             # Task Pydantic schemas
│   ├── services/
│   │   ├── __init__.py
│   │   ├── project_service.py  # Project CRUD logic
│   │   ├── planner_service.py  # Prompt → project planning stub
│   │   └── task_service.py     # Task DAG + orchestration
│   ├── db/
│   │   ├── __init__.py
│   │   ├── base_class.py       # DeclarativeBase definition (no model imports)
│   │   ├── base.py             # Aggregator: re-exports Base + imports all models
│   │   └── session.py          # Async engine, session factory, get_db dependency
│   └── api/
│       ├── __init__.py
│       ├── router.py           # Root router composition
│       └── routes/
│           ├── __init__.py
│           ├── health.py       # GET /health, GET /health/ready
│           ├── projects.py     # Project CRUD endpoints
│           ├── planner.py      # Prompt intake + planning
│           └── tasks.py        # Task query + state management
└── README.md
```

## Tech Stack

- **FastAPI** (Python 3.12)
- **Pydantic v2** + **pydantic-settings** for validation and config
- **SQLAlchemy 2.0** (async) + **asyncpg** for PostgreSQL
- **python-socketio** for WebSocket — _planned_
- **LiteLLM** for LLM gateway — _planned_

## Development

### Via Docker Compose (recommended)

```bash
# From repo root — starts API + all dependencies
docker compose up -d api

# Tail logs
docker compose logs -f api
```

### Locally (without Docker)

```bash
# From repo root
make install-api
make dev-api

# Or manually
cd apps/api
pip install -e ".[dev]"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Requires Postgres and Redis running locally or via `docker compose up -d postgres redis`.

## Database Migrations

Migrations are managed with **Alembic** (async-compatible).

```bash
# From repo root using Makefile
make migrate                          # Apply all pending migrations
make migrate-create msg="add users"   # Auto-generate a new migration

# Or manually from apps/api/
cd apps/api
alembic upgrade head                  # Apply all pending migrations
alembic revision --autogenerate -m "description"  # Generate migration
alembic downgrade -1                  # Roll back one migration
alembic history                       # Show migration history
alembic current                       # Show current DB revision
```

## Local Validation

Quick steps to verify the backend starts and migrates correctly:

```bash
# 1. Start Postgres + Redis
docker compose up -d postgres redis

# 2. Install API deps
make install-api

# 3. Apply migrations
make migrate

# 4. Start the API
make dev-api

# 5. Verify endpoints
curl http://localhost:8000/health
curl http://localhost:8000/health/ready
curl http://localhost:8000/docs          # Swagger UI
```

## Available Endpoints

| Method | Path                         | Description                                     |
| ------ | ---------------------------- | ----------------------------------------------- |
| GET    | `/health`                    | Shallow service health check                    |
| GET    | `/health/ready`              | Deep readiness check (DB ping)                  |
| POST   | `/projects`                  | Create a new project                            |
| GET    | `/projects`                  | List projects (paginated)                       |
| GET    | `/projects/{id}`             | Get project by ID                               |
| PATCH  | `/projects/{id}`             | Update project fields                           |
| POST   | `/planner/intake`            | Submit prompt → creates project + run + tasks   |
| GET    | `/runs/{run_id}/tasks`       | List all tasks for a run                        |
| GET    | `/runs/{run_id}/tasks/ready` | Get tasks ready to execute (deps satisfied)     |
| GET    | `/tasks/{id}`                | Get task by ID                                  |
| PATCH  | `/tasks/{id}/status`         | Transition task status (state-machine enforced) |

## API Docs

Once running, visit:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Configuration

Settings are loaded from environment variables (see root `.env.example`).
Key variables for the API:

| Variable            | Default                 | Description                     |
| ------------------- | ----------------------- | ------------------------------- |
| `APP_ENV`           | `development`           | Environment name                |
| `DEBUG`             | `true`                  | Debug mode                      |
| `API_HOST`          | `0.0.0.0`               | Server bind host                |
| `API_PORT`          | `8000`                  | Server bind port                |
| `CORS_ORIGINS`      | `http://localhost:3000` | Comma-separated allowed origins |
| `POSTGRES_HOST`     | `localhost`             | PostgreSQL host                 |
| `POSTGRES_PORT`     | `5432`                  | PostgreSQL port                 |
| `POSTGRES_DB`       | `forgemind`             | Database name                   |
| `POSTGRES_USER`     | `forgemind`             | Database user                   |
| `POSTGRES_PASSWORD` | `change-me`             | Database password               |
| `DATABASE_URL`      | _(auto-constructed)_    | Full async connection string    |

## Database

The API uses **async SQLAlchemy 2.0** with **asyncpg** for PostgreSQL.

- Engine & session factory: `app/db/session.py`
- Declarative base: `app/db/base.py`
- FastAPI dependency: `get_db` from `app.db.session`

The `DATABASE_URL` is auto-constructed from individual `POSTGRES_*` vars if not set explicitly.
When running via Docker Compose, the compose file sets `DATABASE_URL` pointing at the `postgres` service.
