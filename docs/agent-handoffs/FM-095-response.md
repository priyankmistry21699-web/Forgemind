# FM-095 — Patch Generation & Management

## Summary

Implemented a complete git patch workflow — generate patches from `git diff`, list/preview/apply/reject with metadata tracking and safety validation.

## Deliverables

### Service (`apps/local/forgemind_local/local_patch.py` — 157 lines)

- **`generate_patch(repo_root, scope="staged", author=None)`** — creates `.patch` file + `.json` metadata; returns `{"patch_id", "patch_path", "meta"}`
- **`list_patches(repo_root)`** — enumerates all patches with their metadata
- **`preview_patch(repo_root, patch_id)`** — returns raw diff content
- **`apply_patch(repo_root, patch_id)`** — runs `git apply --check` first, then `git apply`; updates metadata status
- **`reject_patch(repo_root, patch_id)`** — sets status="rejected" in metadata; returns None

### Metadata Tracking

Each patch has a companion `.json` file with: patch_id, scope, author, status (pending/applied/rejected), created_at, applied_at

### CLI

- **`forgemind patch generate`** — create patch from working changes
- **`forgemind patch list`** — show all patches with status
- **`forgemind patch preview <id>`** — display raw diff
- **`forgemind patch apply <id>`** — apply with safety check
- **`forgemind patch reject <id>`** — mark as rejected

## Tests

4 tests in `TestLocalPatch`:
- generate_and_list, preview_patch, apply_and_reject, patch_metadata_tracking

## Test Results

- **Total**: 535 passing
