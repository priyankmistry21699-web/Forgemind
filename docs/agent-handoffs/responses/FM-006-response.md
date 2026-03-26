TASK ID:
FM-006

STATUS:
done

SUMMARY:
Set up Alembic for async database migrations. Created alembic.ini, async-compatible env.py (using async_engine_from_config + asyncio.run), script.py.mako template, and versions directory. Alembic reads DATABASE_URL dynamically from app.core.config.settings and uses Base.metadata from app.db.base for autogenerate support. Migration commands documented in README.

FILES CHANGED:

- apps/api/alembic.ini (created — Alembic config with UTC timestamps, logging config)
- apps/api/alembic/env.py (created — async migration env using asyncio.run + NullPool)
- apps/api/alembic/script.py.mako (created — migration file template)
- apps/api/alembic/versions/.gitkeep (created — empty dir for migration files)
- apps/api/README.md (updated — added Database Migrations section, updated project structure)

IMPLEMENTATION NOTES:

- env.py uses async_engine_from_config with NullPool (migrations are short-lived, no pooling needed)
- sqlalchemy.url is NOT set in alembic.ini — it's injected at runtime from settings.database_url
- prepend_sys_path = . in alembic.ini ensures app.\* imports work from the api root
- file_template uses year_month_day_hourminute_rev_slug for readable filenames
- Both offline (SQL script) and online (async connection) modes are supported
- Makefile already had migrate/migrate-create targets from FM-001

ASSUMPTIONS:

- Migrations are always run from the apps/api/ directory (or via Makefile from repo root)
- Only PostgreSQL+asyncpg driver is needed (no sync fallback)
- All models will be imported in db/base.py for metadata population

BLOCKERS:

- None

NEXT RECOMMENDED STEP:

- FM-007: Create core SQLAlchemy models
