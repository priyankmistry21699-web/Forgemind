# FM-067 — PR Draft Generation

## What was done

Added automatic PR draft generation from patch proposals — builds structured PR title, body, file list, and optional checklist from patch metadata. New service method + REST endpoint.

## Files modified

- `apps/api/app/services/code_ops_service.py` — Added `generate_pr_draft(db, patch_id, target_branch, include_checklist)`:
  - Loads the PatchProposal by ID
  - Builds PR title from patch title
  - Assembles body with description, file list, and optional review checklist
  - Creates a PRDraft record with draft status and linked patch
  - Returns the created PRDraft
- `apps/api/app/schemas/code_ops.py` — Added `PRDraftGenerateRequest` schema (patch_id: UUID, target_branch: str, include_checklist: bool = True).
- `apps/api/app/api/routes/code_ops.py` — Added `POST /projects/{project_id}/pr-drafts/generate` endpoint.

## Design decisions

- Template-based generation (not LLM-powered) — deterministic, fast, no API key dependency; LLM enhancement is tracked as TD-021
- Checklist items auto-generated from target_files list (one item per file: "Review changes in {file}")
- PR body structure mirrors GitHub/GitLab conventions (description, file list, checklist sections)
- Returns the full PRDraft object so the caller can review/edit before submission
