# FM-092 — Repo Indexing & Manifest

## Summary

Implemented local repository indexing that walks the file tree, classifies files by language, detects entrypoints and build files, and caches a JSON manifest for fast subsequent access.

## Deliverables

### Service (`apps/local/forgemind_local/repo_index.py` — 127 lines)

- **`build_repo_index(repo_root)`** — walks tree, classifies 30+ file extensions, detects 6 entrypoint patterns and 11 build file patterns, prunes 15 ignored directories (node_modules, .git, __pycache__, etc.)
- **`load_manifest(repo_root)`** — reads cached `repo_manifest.json`; returns None if missing
- Manifest structure: `{files: [{path, language, lines, is_entrypoint, is_build_file}], summary: {total_files, languages, entrypoints, build_files}, indexed_at}`

### CLI

- **`forgemind attach`** — calls `build_repo_index`, prints summary table with file counts and language breakdown

## Tests

7 tests in `TestRepoIndex`:
- build_index, entrypoints_detected, build_files_detected, ignore_dirs_skipped, load_manifest_missing, load_manifest_present, build_index_file_count

## Test Results

- **Total**: 535 passing
