# FM-066 — Branch Strategy Manager

## What was done

Added branch management configuration to RepoConnection with BranchMode enum, template-based branch naming, and tracking of the last generated branch name.

## Files modified

- `apps/api/app/models/repo_connection.py` — Added `BranchMode` enum (DIRECT, FEATURE_BRANCH, REVIEW_BRANCH). Added 3 new columns: `branch_mode` (BranchMode enum, default DIRECT), `target_branch_template` (string template e.g. "feature/{task_id}"), `last_generated_branch` (most recently created branch name).
- `apps/api/app/schemas/repo.py` — Added `branch_mode`, `target_branch_template`, `last_generated_branch` to Read/Create/Update schemas.
- `apps/api/app/services/repo_service.py` — Updated `create_connection()` and `update_connection()` to accept and persist branch strategy fields.

## Design decisions

- BranchMode is per-connection, not per-project — different repos in the same project may use different branching strategies
- `target_branch_template` uses simple string templates (not Jinja) — resolved at branch creation time with context variables
- DIRECT mode = push to default branch; FEATURE_BRANCH = create `feature/*` branches; REVIEW_BRANCH = create `review/*` branches for code review
- `last_generated_branch` enables follow-up operations (PR creation, status checks) without re-querying the branch name
