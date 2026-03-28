# FM-062 — File Tree Explorer

## What was done

Added local filesystem browsing for connected repositories — directory listing, file content reading, metadata inspection, and context snippet building, all with path traversal protection and size limits.

## Files modified

- `apps/api/app/services/repo_service.py` — Added 4 new functions:
  - `get_file_tree(db, connection_id, path)`: Lists directory contents with type detection (file/directory), size, and language inference. Enforces MAX_TREE_ENTRIES (500) and path traversal checks.
  - `get_file_content(db, connection_id, path)`: Reads file content with MAX_FILE_SIZE_BYTES (1MB) limit.
  - `get_file_metadata(db, connection_id, path)`: Returns stat info (size, modified time, permissions).
  - `build_context_snippet(db, connection_id, path, start_line, end_line)`: Extracts specific line ranges for AI context injection.
  - Added `_LANG_MAP` dict mapping 20+ file extensions to language names.
- `apps/api/app/schemas/repo.py` — Added `FileTreeEntry` (name, path, type, size, language), `FileTreeResult` (entries list + current_path), `FileContentResult` (path, content, language, size).
- `apps/api/app/api/routes/repos.py` — Added `GET /repos/{id}/tree?path=`, `GET /repos/{id}/file?path=`, `GET /repos/{id}/file-meta?path=` endpoints.

## Files created

- `apps/web/app/dashboard/code-explorer/page.tsx` — Frontend split-panel file explorer with repo selector, directory tree (breadcrumb navigation, up-navigation), and file content viewer with syntax info.

## Design decisions

- Path traversal protection: all resolved paths checked against `workspace_path` base via `Path.resolve()` + `relative_to()` — prevents `../` attacks
- MAX_FILE_SIZE_BYTES (1MB) prevents accidental loading of binary blobs into memory
- MAX_TREE_ENTRIES (500) prevents browser-crashing directory listings
- Language detection via extension map (not content inspection) — fast and sufficient for most cases
- `.resolve()` called on both base and target paths to handle Windows short path names (VISHVA~1 vs VISHVA MISTRY)
