# FM-024 — Worker / Orchestrator Foundation — Response

**Status:** DONE
**Date:** 2025-07-15

---

## Files Created

| File                                    | Purpose                                                              |
| --------------------------------------- | -------------------------------------------------------------------- |
| `apps/worker/worker/__init__.py`        | Package init                                                         |
| `apps/worker/worker/main.py`            | Worker loop: poll → resolve agent → claim → dispatch → complete/fail |
| `apps/worker/worker/agents/__init__.py` | dispatch_agent() — handler lookup + fallback stub                    |
| `apps/worker/worker/agents/registry.py` | AGENT_HANDLERS dict mapping slug → handler                           |

## Files Modified

| File                    | Change                                                             |
| ----------------------- | ------------------------------------------------------------------ |
| `docker-compose.yml`    | Added worker service (6th service) with volume mounts and env vars |
| `apps/worker/README.md` | Rewritten from Celery placeholder to async polling worker docs     |

## Design Decisions

1. **Async polling loop** over Celery — much simpler for MVP. Worker runs `asyncio.sleep(POLL_INTERVAL)` between cycles. Configurable via `WORKER_POLL_INTERVAL` (default 5s) and `WORKER_MAX_TASKS_PER_CYCLE` (default 3).
2. **Shares apps/api code** via sys.path manipulation + Docker volume mount — avoids code duplication. Worker imports models, services, and DB session factory directly from the API package.
3. **Agent dispatch pattern**: `dispatch_agent(db, task, agent)` looks up `AGENT_HANDLERS[agent.slug]`. Unknown slugs get a stub response rather than failing.
4. **Error isolation**: Each task dispatch is wrapped in try/except. Failures call `execution_service.fail_task()` in a separate session, ensuring failure state is always persisted.
5. **Docker worker service** uses same base image as API, different entrypoint (`python -m worker.main`), mounts both `./apps/api` and `./apps/worker`.

## Acceptance Criteria Met

- [x] Worker loop polls for READY tasks at configurable interval
- [x] process_ready_tasks() resolves agent, claims, dispatches, completes
- [x] dispatch_agent() delegates to registered handler or stub
- [x] Failed dispatches mark task as FAILED with error message
- [x] Docker Compose worker service configured with proper mounts and env
- [x] README updated with worker architecture docs
