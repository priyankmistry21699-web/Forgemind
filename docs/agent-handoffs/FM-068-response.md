# FM-068 — Repo Action Approval Gates

## What was done

Added an approval gate check service that queries the latest RepoActionApproval for a given project and action type, returning whether the action is allowed to proceed.

## Files modified

- `apps/api/app/services/code_ops_service.py` — Added `check_approval_gate(db, project_id, action_type)`:
  - Queries latest RepoActionApproval for the project + action type (ordered by created_at DESC)
  - Returns dict with `allowed` (bool), `approval_id`, `status`, `decided_by`, `decided_at`
  - Returns `allowed: True` with no approval_id if no gate exists (permissive default)
- `apps/api/app/api/routes/code_ops.py` — Added `GET /projects/{project_id}/repo-approvals/check?action_type=push` endpoint.

## Design decisions

- Permissive default: if no approval record exists for an action, the gate is open — avoids blocking new projects that haven't configured gates
- Only checks the latest approval per action type (not all historical records) — keeps queries simple and reflects current state
- `action_type` passed as query parameter (not path) for flexibility — same endpoint checks push, merge, deploy, release, delete_branch
- Returns approval metadata (decided_by, decided_at) for audit trail purposes
