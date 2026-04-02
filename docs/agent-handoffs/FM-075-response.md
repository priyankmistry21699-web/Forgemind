# FM-075 — Route-Level RBAC Enforcement Hardening

## Summary

Hardened the entire ForgeMind API with authentication on all non-public endpoints and wired up the existing RBAC system (authz_service) for sensitive operations.

## Changes

### Extended authz_service (`app/services/authz_service.py`)

- Added 5 new Actions: `WORKSPACE_MANAGE_SECRETS`, `WORKSPACE_VIEW_AUDIT`, `PROJECT_EXECUTE_CODE`, `PROJECT_MANAGE_KNOWLEDGE`, `PROJECT_MANAGE_ESCALATION`
- Updated permission matrices with appropriate role access

### Created authz dependency helpers (`app/core/authz_deps.py`)

- `resolve_workspace_for_project()` — project → workspace_id
- `resolve_project_for_run()` — run → project_id
- `resolve_project_for_task()` — task → run → project_id

### Route Hardening (23 route files, 164 non-public endpoints)

Every non-public endpoint now requires `user_id: uuid.UUID = Depends(get_current_user_id)`:

| Route File          | Endpoints Secured                  |
| ------------------- | ---------------------------------- |
| workspaces.py       | 3 (get/patch/delete + RBAC checks) |
| members.py          | 8 (all + workspace/project RBAC)   |
| credential_vault.py | 7                                  |
| governance.py       | 9                                  |
| audit.py            | 3                                  |
| approvals.py        | 3                                  |
| escalation.py       | 7                                  |
| projects.py         | 2 (get/patch)                      |
| tasks.py            | 10                                 |
| runs.py             | 3                                  |
| repos.py            | 13                                 |
| code_ops.py         | 25                                 |
| trust.py            | 5                                  |
| streaming.py        | 2                                  |
| run_lifecycle.py    | 4                                  |
| replay.py           | 7                                  |
| notifications.py    | 1 (mark_read)                      |
| memory.py           | 3                                  |
| knowledge.py        | 6                                  |
| council.py          | 6                                  |
| costs.py            | 4                                  |
| connectors.py       | 6                                  |
| composition.py      | 2                                  |
| chat.py             | 1                                  |
| artifacts.py        | 5                                  |
| agents.py           | 2                                  |
| events.py           | 1                                  |
| activity.py         | 5                                  |

### RBAC Enforcement (workspace/project-level checks)

- `workspaces.py`: `WORKSPACE_VIEW`, `WORKSPACE_UPDATE`, `WORKSPACE_DELETE`
- `members.py`: `WORKSPACE_MANAGE_MEMBERS`, `WORKSPACE_VIEW`, `PROJECT_MANAGE_MEMBERS`, `PROJECT_VIEW`

### Public endpoints (correctly left open)

- `GET /health`, `GET /health/ready`
- `POST /auth/register`, `POST /auth/login`

## Tests

- **33/33** new RBAC tests pass (`test_fm075_rbac.py`)
  - Permission matrix completeness
  - Workspace RBAC (owner/admin/operator/reviewer/viewer)
  - Project RBAC (lead/operator/reviewer/viewer)
  - Route auth enforcement (multiple endpoint groups)
  - Role resolution helpers
  - Negative access tests (wrong role → 403, non-member → 404)
- **34/34** regression tests pass (`test_fm046_050_v2.py`)
- **10/10** auth tests pass (`test_fm074_auth.py`)
- **77/77 total** tests passing
