# FM-065 — Change Review Workspace

## What was done

Enhanced ChangeReview with file-level annotation support (file path, line range, code suggestions) and built a frontend review workspace page with diff viewing and inline annotations.

## Files modified

- `apps/api/app/models/code_ops.py` — Added 4 new columns to ChangeReview: `file_path` (specific file being annotated), `line_start` (starting line number), `line_end` (ending line number), `suggestion` (proposed replacement code).
- `apps/api/app/schemas/code_ops.py` — Added all 4 new fields to `ChangeReviewCreate` and `ChangeReviewRead` schemas.
- `apps/api/app/services/code_ops_service.py` — Updated `create_review()` to pass FM-065 annotation fields.
- `apps/api/app/api/routes/code_ops.py` — Updated review creation endpoint to extract and pass annotation fields.

## Files created

- `apps/web/app/dashboard/reviews/[patchId]/page.tsx` — Review workspace page with:
  - Patch info header (title, status, readiness state, target files)
  - Diff viewer (pre-formatted diff content)
  - File annotations section (grouped by file path with line range display)
  - Suggestion rendering (green-highlighted code blocks)
  - General reviews section (non-file-specific comments)
  - Decision badges (approve, request_changes, comment)

## Design decisions

- `file_path` + `line_start`/`line_end` on ChangeReview (not a separate annotation model) — keeps the review model simple; one review can annotate one specific code location
- `suggestion` is free-text (not structured diff) — allows both code snippets and natural language suggestions
- Frontend uses dynamic route `[patchId]` for direct linking to specific patch reviews
- File annotations and general reviews split into separate sections for clarity
