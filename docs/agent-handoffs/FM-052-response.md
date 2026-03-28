# FM-052 — Workspace Member Roles & Authorization

## What was done

Created a workspace membership model with 5 hierarchical roles and a central authorization service with declarative permission matrices, enabling role-based access control across the platform.

## Files created

- `apps/api/app/models/membership.py` — `WorkspaceMember` model:
  - `workspace_id` FK, `user_id` FK, `role` enum
  - `UniqueConstraint("workspace_id", "user_id")` prevents duplicate memberships
  - Role enum: `OWNER`, `ADMIN`, `OPERATOR`, `REVIEWER`, `VIEWER` (5 tiers)
- `apps/api/app/services/authz_service.py` — Central authorization service:
  - `WORKSPACE_PERMISSIONS` dict: Declarative permission matrix mapping roles to allowed actions
  - Actions: `UPDATE`, `DELETE`, `MANAGE_MEMBERS`, `MANAGE_GOVERNANCE`, `MANAGE_CONNECTORS`, `MANAGE_REPOS`, `CREATE_PROJECT`, `VIEW`
  - `check_workspace_permission(db, workspace_id, user_id, action)`: Enforces permission matrix; returns 403 (insufficient permission) or 404 (not a member)
- Membership service functions: Add, get, list, update role, remove workspace members
- Schemas and routes for workspace member CRUD

## Files modified

- `apps/api/alembic/versions/2026_03_27_0019_add_collaboration_and_code_ops.py` — Creates `workspace_members` table
- `apps/api/app/db/base.py` — Added `WorkspaceMember` import
- `apps/api/app/api/router.py` — Registered members routes

## Design decisions

- Declarative permission matrix (dict-based) for auditability and easy modification
- Default role is `VIEWER` (secure by default)
- Role hierarchy: `OWNER > ADMIN > OPERATOR > REVIEWER > VIEWER`
- Authorization returns 403 Forbidden (insufficient permission) vs 404 (not a member) for clear error signaling
