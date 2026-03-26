TASK ID:
FM-005

STATUS:
done

SUMMARY:
Set up async SQLAlchemy 2.0 database foundation with declarative base, async engine/session factory, FastAPI dependency injection, config integration with auto-constructed DATABASE_URL, and a /health/ready deep readiness endpoint. Engine is properly disposed on app shutdown.

FILES CHANGED:

- apps/api/app/db/**init**.py (created)
- apps/api/app/db/base.py (created — declarative Base class)
- apps/api/app/db/session.py (created — async engine, session factory, get_db dependency)
- apps/api/app/core/config.py (updated — added postgres/redis settings, auto-construct DATABASE_URL)
- apps/api/app/api/routes/health.py (updated — added GET /health/ready with DB ping)
- apps/api/app/main.py (updated — engine.dispose() on shutdown in lifespan)
- apps/api/pyproject.toml (updated — added sqlalchemy[asyncio], asyncpg, alembic)
- apps/api/README.md (updated — project structure, endpoints, config table, database section)

IMPLEMENTATION NOTES:

- Async engine uses pool_pre_ping=True for connection liveness, pool_size=5, max_overflow=10
- Session dependency (get_db) auto-commits on success, rolls back on exception
- expire_on_commit=False so objects remain usable after commit within the same request
- DATABASE*URL auto-constructed from POSTGRES*\* vars via model_post_init if not explicitly set
- /health remains a shallow check (no deps); /health/ready does SELECT 1 against Postgres
- Alembic added to deps proactively since FM-006 needs it next
- echo=settings.debug so SQL logging is on in dev, off in production

ASSUMPTIONS:

- PostgreSQL is available via Docker Compose or locally on the configured host/port
- asyncpg is the only async Postgres driver needed (no psycopg3)
- The get_db dependency pattern handles one session per request with auto-commit
- No connection pooling tuning needed yet beyond sensible defaults

BLOCKERS:

- None

NEXT RECOMMENDED STEP:

- FM-006: Set up Alembic for schema migrations
