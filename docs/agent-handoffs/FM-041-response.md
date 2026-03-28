# FM-041 — Connector Readiness States

## What was done

Introduced a per-project connector tracking system via a join table model (`ProjectConnectorLink`) that tracks the readiness lifecycle of each connector attached to a project, replacing ad-hoc connector status checks.

## Files created

- `apps/api/app/models/project_connector_link.py` — `ProjectConnectorLink` model:
  - `ConnectorReadiness` enum: `MISSING`, `CONFIGURED`, `BLOCKED`, `READY`
  - `ConnectorPriority` enum: `REQUIRED`, `RECOMMENDED`, `OPTIONAL`
  - Table `project_connector_links` with `UniqueConstraint("project_id", "connector_id")`
  - FKs to `projects` (CASCADE) and `connectors` (CASCADE)
  - `config_snapshot` (JSON) and `blocker_reason` (Text) fields
- `apps/api/alembic/versions/2026_03_28_0008_0009_add_project_connector_links.py` — Migration creating `project_connector_links` table

## Files modified

- `apps/api/app/db/base.py` — Added `ProjectConnectorLink` import for Alembic metadata registration

## Design decisions

- M:N join table between projects and connectors rather than a status field on the connector model — allows per-project connector state
- Unique constraint ensures one link per project-connector pair
- `blocker_reason` field documents why a connector is in `BLOCKED` state
- Readiness state machine: `MISSING → CONFIGURED → READY` with `BLOCKED` as a side state
- No dedicated service or route — connector readiness is managed through existing `connector_service.py` (`get_project_connector_requirements`)
