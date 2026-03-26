TASK ID:
FM-004

STATUS:
done

SUMMARY:
Upgraded the Docker Compose local development stack from infra-only to a full 5-service setup (Postgres, Redis, MinIO, API, Web). Added Dockerfiles for the API and Web apps, wired environment variables via .env defaults, added health checks and dependency ordering, and updated all relevant documentation.

FILES CHANGED:

- docker-compose.yml (upgraded — added api + web services, env var substitution, dependency chain, health checks, port docs)
- apps/api/Dockerfile (created)
- apps/web/Dockerfile (created)
- .env.example (updated — added Docker Compose note in header)
- README.md (updated — added Docker-first quick start + alternative local instructions)
- apps/api/README.md (updated — added Docker Compose dev section)
- apps/web/README.md (updated — added Docker Compose dev section)

IMPLEMENTATION NOTES:

- Compose uses ${VAR:-default} syntax so it works with or without a .env file
- API service depends on postgres (healthy) + redis (healthy); Web depends on api (healthy)
- API health check uses curl against /health endpoint with start_period to allow boot time
- Both api and web mount source code as volumes for hot-reload in development
- Web uses anonymous volume for node_modules to avoid host/container conflicts (/app/node_modules)
- All ports are documented in the compose file header comment block
- Infrastructure services (postgres, redis, minio) unchanged structurally, just parameterized with env vars
- Dockerfiles are dev-focused (--reload for uvicorn, npm run dev for next)

ASSUMPTIONS:

- Docker and Docker Compose v2 are available on the dev machine
- .env file will be copied from .env.example before first docker compose up
- Dockerfiles are development-only; production Dockerfiles will be separate (multi-stage) in a future task
- No worker service yet — will be added when Celery is integrated (FM-005+)
- The API Dockerfile uses pip install -e ".[dev]" which requires the source to be present at build time

BLOCKERS:

- None

NEXT RECOMMENDED STEP:

- FM-005: Add SQLAlchemy base/session config (connect the API to Postgres)
