# FM-051 — Workspace Model (Multi-Tenant Workspaces)

## What was done

Introduced the `Workspace` model as the top-level organizational unit for multi-tenancy. Workspaces own projects via a new FK on the Project model, enabling team-scoped isolation.

## Files created

- `apps/api/app/models/workspace.py` — `Workspace` model:
  - `name`, `slug` (unique), `description`, `owner_id` (UUID)
  - `status` enum: `active`, `suspended`, `archived`
  - `settings` (JSON) for workspace-level configuration
  - Timestamps: `created_at`, `updated_at`
- `apps/api/app/services/workspace_service.py` — Workspace service:
  - `create_workspace()`, `get_workspace()`, `get_workspace_by_slug()`, `list_workspaces()`, `update_workspace()`, `delete_workspace()`
  - Slug uniqueness enforced (409 Conflict on duplicate)
- `apps/api/app/schemas/workspace.py` — Create/read/update schemas
- `apps/api/app/api/routes/workspaces.py` — Routes: `POST /workspaces`, `GET /workspaces`, `GET /workspaces/{id}`, `PATCH /workspaces/{id}`, `DELETE /workspaces/{id}`

## Files modified

- `apps/api/alembic/versions/2026_03_27_0019_add_collaboration_and_code_ops.py` — Creates `workspaces` table (part of the collaboration mega-migration)
- `apps/api/alembic/versions/2026_03_28_0020_add_workspace_id_to_projects.py` — Adds `workspace_id` FK + index to `projects` table
- `apps/api/app/db/base.py` — Added `Workspace` import
- `apps/api/app/api/router.py` — Registered `workspaces_router`

## Design decisions

- Slug-based URLs for human readability (`/workspaces/my-team`)
- Status enum allows workspace suspension/archival without deletion
- Settings JSON provides flexibility for future workspace-level configuration
- `workspace_id` on projects is nullable to avoid breaking existing projects
