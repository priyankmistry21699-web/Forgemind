# FM-053 — Project-Level Members & Approvers

## What was done

Added project-level membership with 4 roles and independent approver/reviewer flags, enabling fine-grained per-project access control that complements workspace-level RBAC from FM-052.

## Files created / modified

- `apps/api/app/models/membership.py` — Added `ProjectMember` model (same file as `WorkspaceMember`):
  - `project_id` FK, `user_id` FK, `role` enum
  - `UniqueConstraint("project_id", "user_id")`
  - Role enum: `LEAD`, `OPERATOR`, `REVIEWER`, `VIEWER` (4 roles)
  - `is_approver` (bool) and `is_reviewer` (bool) flags for workflow-specific permissions
- `apps/api/app/services/membership_service.py` — Project member service:
  - Add project member, list, update (role + flags), remove
  - Workspace membership validation on add
- `apps/api/app/services/authz_service.py` — Added `PROJECT_PERMISSIONS` matrix:
  - Separate permission matrix for project-level actions
  - Project roles are independent of workspace roles

## Files modified

- `apps/api/alembic/versions/2026_03_27_0019_add_collaboration_and_code_ops.py` — Creates `project_members` table
- `apps/api/app/db/base.py` — Added `ProjectMember` import

## Design decisions

- 4 project-specific roles vs 5 workspace roles — projects don't need OWNER/ADMIN distinction
- Approval/reviewer flags are independent of role, enabling combinations like `VIEWER + is_reviewer=True`
- Workspace membership is validated when adding project members — users must belong to the workspace first
