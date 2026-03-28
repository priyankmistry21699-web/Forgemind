# FM-064 — Patch Proposal Engine

## What was done

Enhanced PatchProposal with rich metadata for tracking which files a patch touches, its format, readiness state, and the agent that proposed it. Enables more informed review workflows.

## Files modified

- `apps/api/app/models/code_ops.py` — Added `PatchFormat` enum (UNIFIED, SIDE_BY_SIDE, RAW), `ReadinessState` enum (INCOMPLETE, NEEDS_REVIEW, READY, BLOCKED). Added 5 new columns to PatchProposal: `target_files` (JSON array of affected file paths), `patch_format` (PatchFormat enum), `proposed_by_agent` (agent slug), `readiness_state` (ReadinessState enum), `linked_artifact_ids` (JSON array of artifact UUIDs).
- `apps/api/app/schemas/code_ops.py` — Added all 5 new fields to `PatchProposalCreate` and `PatchProposalRead` schemas.
- `apps/api/app/services/code_ops_service.py` — Updated `create_patch()` to pass FM-064 fields. Updated allowed update fields to include new columns.
- `apps/api/app/api/routes/code_ops.py` — Updated patch creation endpoint to extract and pass new fields from request body.

## Design decisions

- `target_files` as JSON array (not a junction table) — simple for reads, patches rarely touch >20 files
- `ReadinessState` is distinct from `status` — status tracks workflow (draft→approved→merged) while readiness tracks completeness (incomplete→ready)
- `linked_artifact_ids` stored as JSON array rather than a junction table for simplicity — enables cross-referencing without complex joins
- `proposed_by_agent` enables attribution tracking for multi-agent patch generation scenarios
