# FM-038 — Connector Intelligence Foundation

## What was done

Created a connector registry and recommendation engine that maps project characteristics to external tool/service requirements.

## Files created

- `apps/api/app/models/connector.py` — Connector model with status enum (available/configured/unavailable), capabilities JSON, config JSON
- `apps/api/app/schemas/connector.py` — ConnectorRead, ConnectorList, ConnectorRecommendation schemas
- `apps/api/app/services/connector_service.py` — Connector service:
  - 7 default connectors: GitHub, Docker, PostgreSQL, Redis, Object Storage, Slack, Jira
  - `STACK_CONNECTOR_MAP`: Keyword → connector recommendation mapping
  - `recommend_connectors(stack, description)`: Keyword analysis with dedup and priority sorting
  - `get_project_connector_requirements(db, stack, description)`: Recommendations with configured status
- `apps/api/app/api/routes/connectors.py` — REST endpoints:
  - `GET /connectors` → list all registered connectors
  - `GET /runs/{run_id}/connectors/requirements` → project-specific recommendations
- `apps/api/alembic/versions/2026_03_27_0007_0008_add_connectors.py` — Migration for connectors table

## Files modified

- `apps/api/app/db/base.py` — Added Connector model import
- `apps/api/app/api/router.py` — Mounted connectors_router

## Design decisions

- Connectors seeded on first list if table is empty (self-bootstrapping)
- Recommendations are keyword-based with priority levels (required > recommended > optional)
- Connector model stores capabilities as JSON for flexible schema evolution
