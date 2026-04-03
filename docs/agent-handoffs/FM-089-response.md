# FM-089 — Architecture Approval Workflow

## Summary

Implemented automatic approval request creation when change impact analysis reveals HIGH or CRITICAL severity. Integrates with the existing approval_service to gate high-impact architectural changes behind human review.

## Deliverables

### Service (`apps/api/app/services/architecture_approval_service.py`)

- **`maybe_create_approval(db, project_id, assessment)`** — Checks a ChangeImpactAssessment's severity; if HIGH or CRITICAL, auto-creates an ApprovalRequest with architecture context (target node, blast radius, impacted services); returns the approval if created, None otherwise
- **`list_architecture_approvals(db, project_id)`** — Retrieve ApprovalRequest records whose titles contain architecture-related keywords ("Architecture", "Impact"); filters to project scope

### Integration

- Uses existing `ApprovalRequest` model from `apps/api/app/models/approval.py`
- Uses existing `ApprovalRead` and `ApprovalList` schemas from `apps/api/app/schemas/approval.py`
- Approval lifecycle (approve/reject/decide) handled by existing `approval_service`

### Route Endpoints (2)

- `POST /projects/{pid}/architecture/approvals` — Request architecture approval (auto-creates if severity warrants)
- `GET /projects/{pid}/architecture/approvals` — List architecture-related approvals

## Tests

3 tests covering:

- `TestArchitectureApprovalService` (2 tests) — no approval created for LOW severity, approval created for HIGH severity
- `TestArchitectureApprovalRoutes` (1 test) — list approvals route

## Test Results

- **Total**: 482 passing
- **Regression**: None
