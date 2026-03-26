# ForgeMind Worker

> Lightweight background task execution loop for ForgeMind.

## Overview

Polls for READY tasks, resolves the appropriate agent, claims the task,
dispatches it for execution, and marks it complete or failed.

## How It Works

1. Worker loop polls DB for `READY` tasks every N seconds
2. Resolves agent via `agent_service.resolve_agent_for_task_type()`
3. Claims task via `execution_service.claim_task()`
4. Dispatches to agent handler via `worker.agents.dispatch_agent()`
5. Completes task via `execution_service.complete_task()` (creates artifact)
6. On failure: marks task failed with error message

## Running Locally

```bash
# From apps/worker/ (with apps/api on PYTHONPATH)
cd apps/worker
PYTHONPATH=../api python -m worker.main
```

## Running via Docker Compose

```bash
docker compose up worker
```

## Configuration

| Env Var                      | Default    | Description                    |
| ---------------------------- | ---------- | ------------------------------ |
| `WORKER_POLL_INTERVAL`       | `5`        | Seconds between poll cycles    |
| `WORKER_MAX_TASKS_PER_CYCLE` | `3`        | Max tasks to process per cycle |
| `DATABASE_URL`               | (required) | PostgreSQL connection string   |

## Tech Stack

- **Python 3.12** async worker loop
- Shares `apps/api` packages (models, services, config)
- **No Celery** for MVP — simple `asyncio.sleep` poll loop
- Agent handlers registered in `worker/agents/registry.py`

## Development

```bash
# From repo root
make dev-worker

# Or directly
cd apps/worker
celery -A worker.main worker --loglevel=info
```
