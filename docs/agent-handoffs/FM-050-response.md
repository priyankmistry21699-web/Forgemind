# FM-050 — Production Hardening

## What was done

Added production-grade infrastructure: JWT authentication with dev-mode fallback, IP-based rate limiting, request logging with correlation IDs, structured error handlers, and a heuristic trust scoring system for tasks, artifacts, and runs.

## Files created

### Security & Middleware
- `apps/api/app/core/auth.py` — JWT authentication:
  - `create_access_token(user_id, ...)`: Creates HS256 JWT with 24h expiry
  - `decode_token(token)`: Verifies and decodes JWT
  - `get_current_user_id(credentials)`: Dual-mode dependency — returns stub UUID when no JWT configured (dev), requires valid Bearer token in production
- `apps/api/app/core/rate_limit.py` — Rate limiting:
  - `_TokenBucket` class: Capacity + refill rate per IP
  - `RateLimitMiddleware`: 100 req/60s per IP, skips `/health`, returns 429 with `Retry-After`
  - In-memory only (note: needs Redis for multi-instance production)
  - Only enabled when `settings.debug = False`
- `apps/api/app/core/logging_middleware.py` — Request logging:
  - Generates 8-char request ID
  - Logs method, path, status code, elapsed ms
  - Attaches `X-Request-ID` response header
- `apps/api/app/core/error_handlers.py` — Error handlers:
  - `StarletteHTTPException` → structured JSON
  - `RequestValidationError` → 422 with error details
  - All `Exception` → 500 with generic message (no stack trace in response)

### Trust Scoring
- `apps/api/app/models/trust_score.py` — `TrustScore` model:
  - `RiskLevel` enum: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`
  - `EntityType` enum: `TASK`, `ARTIFACT`, `RUN`
  - Generic entity scoring: `entity_type` + `entity_id`, `trust_score` (0–1), `confidence`, `risk_level`, `factors` (JSON breakdown)
- `apps/api/app/services/trust_scoring_service.py` — Trust service:
  - `_classify_risk(score)`: Thresholds ≥0.8=LOW, ≥0.5=MEDIUM, ≥0.3=HIGH, <0.3=CRITICAL
  - `assess_task(db, task_id)`: Weighted heuristic — status (0.4), retry burden (0.25), agent assignment (0.15), error presence (0.2). Upserts
  - `assess_run(db, run_id)`: Aggregate of all task assessments
  - `get_run_risk_summary(db, run_id)`: Comprehensive risk report
- `apps/api/app/api/routes/trust.py` — Routes: `POST /trust/tasks/{id}/assess`, `POST /trust/runs/{id}/assess`, `GET /trust/runs/{id}/risk-summary`, `GET /trust/scores`
- `apps/api/app/schemas/trust.py` — Trust schemas
- `apps/api/alembic/versions/2026_03_29_0013_0014_add_trust_scores.py` — Migration creating `trust_scores`

## Files modified

- `apps/api/app/main.py` — Added `RateLimitMiddleware`, `RequestLoggingMiddleware`, `register_error_handlers()`
- `apps/api/app/db/base.py` — Added `TrustScore` import
- `apps/api/app/api/router.py` — Registered `trust_router`

## Design decisions

- JWT falls back to stub gracefully — no breaking change for dev environments
- Rate limiter is in-memory (acknowledged as needing Redis for multi-instance production)
- Error handler never leaks stack traces to clients (500 returns generic message, logs full traceback server-side)
- Trust scoring uses upsert pattern — re-assessment overwrites previous scores
- Trust factors stored as JSON for full transparency (each factor shows value, score, and weight)
