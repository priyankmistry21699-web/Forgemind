# FM-080 — Production Deployment Foundation

## Summary

Established a complete production deployment baseline with multi-stage Docker
builds, a production Docker Compose stack, nginx reverse proxy with TLS, and
comprehensive deployment documentation.

## Deliverables

### Production Dockerfiles

- **`apps/api/Dockerfile.prod`**: Multi-stage build (builder → runtime), non-root `appuser`, HEALTHCHECK directive, uvicorn with 2 workers
- **`apps/web/Dockerfile.prod`**: Multi-stage build (deps → builder → runtime), Next.js standalone output, non-root `appuser`, build-time `NEXT_PUBLIC_API_URL` arg

### Production Docker Compose (`docker-compose.prod.yml`)

- 6 services: postgres, redis, api, web, worker, nginx
- Required env vars enforced with `${VAR:?message}` syntax (SECRET_KEY, POSTGRES_PASSWORD, CORS_ORIGINS, NEXT_PUBLIC_API_URL)
- Internal Docker network — only nginx exposes ports
- Health checks on all services
- No source code bind-mounts (unlike dev compose)

### Nginx Reverse Proxy (`deploy/nginx.conf`)

- HTTP → HTTPS redirect
- TLS termination with configurable certs
- Security headers: X-Frame-Options, X-Content-Type-Options, HSTS, X-XSS-Protection, Referrer-Policy
- Smart routing: /api/ → API, /stream/ → SSE (with buffering off), / → Web
- Let's Encrypt ACME challenge passthrough

### Deployment Documentation (`docs/DEPLOYMENT.md`)

- Quick start guide (5 steps)
- Environment variable reference (required vs optional)
- Architecture diagram
- Health endpoint documentation
- Security checklist
- TLS setup with Let's Encrypt + auto-renewal cron
- Non-TLS mode instructions
- Prometheus monitoring integration
- Database backup/restore procedures
- Update procedure

### Other Files

- `.env.production` — production env template with required vars marked
- `deploy/certs/.gitkeep` — placeholder for TLS certificates
- `apps/web/next.config.mjs` — added `output: "standalone"` for prod builds

## Tests

16 new tests in `test_fm080_deployment.py`:

- Production compose: exists, services, no source mounts, required env vars
- Dockerfiles: exist, non-root user, healthcheck
- Nginx: exists, security headers, routing
- Docs: deployment README exists and covers essentials
- Env: production example exists and documents required vars

## Test Results

- **385/385 tests passing** (369 existing + 16 new)
- No regressions
