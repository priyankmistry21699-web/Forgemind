# FM-026 — Approval Request Model & Workflow — Response

**Status:** DONE
**Date:** 2025-07-15

---

## Files Created

| File                                                                      | Purpose                                                                       |
| ------------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| `apps/api/app/models/approval_request.py`                                 | ApprovalRequest model with ApprovalStatus enum (pending/approved/rejected)    |
| `apps/api/app/schemas/approval.py`                                        | ApprovalRead, ApprovalList, ApprovalCreate, ApprovalDecision Pydantic schemas |
| `apps/api/app/services/approval_service.py`                               | create_approval, get_approval, list_approvals, resolve_approval               |
| `apps/api/app/api/routes/approvals.py`                                    | GET /approvals, GET /approvals/{id}, POST /approvals/{id}/decide              |
| `apps/api/alembic/versions/2026_03_26_0005_0006_add_approval_requests.py` | Migration 0006: approval_requests table + enum + index                        |

## Files Modified

| File                                         | Change                                                                |
| -------------------------------------------- | --------------------------------------------------------------------- |
| `apps/api/app/db/base.py`                    | Registered ApprovalRequest model import                               |
| `apps/api/app/api/router.py`                 | Mounted approvals router with "approvals" tag                         |
| `apps/api/app/services/execution_service.py` | Auto-create approval for architecture/review task types on completion |

## Design Decisions

1. **Auto-approval on task completion** — When a task with type `architecture` or `review` completes, an approval request is automatically created. Configurable via `APPROVAL_REQUIRED_TASK_TYPES` set.
2. **Approval status enum** — Three states: pending, approved, rejected. Only pending approvals can be resolved.
3. **Flexible filtering** — list_approvals supports project_id, run_id, and status query filters.
4. **Decision tracking** — Stores decided_by (user UUID), decision_comment, and decided_at timestamp.
5. **FK relationships** — Links to project, run, task, and optionally artifact.

## Technical Debt Added

- **TD-013**: Approval required only for fixed task types (no policy engine)
- **TD-015**: Approval decision has no authorization check

## Acceptance Criteria Met

- [x] ApprovalRequest model with pending/approved/rejected states
- [x] CRUD + decision endpoints for approvals
- [x] Auto-creation on architecture/review task completion
- [x] Filtering by project, run, and status
- [x] Migration creates table with proper indexes
