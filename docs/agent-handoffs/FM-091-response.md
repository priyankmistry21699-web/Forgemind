# FM-091 — Local Foundation: Config, Init & Directory Management

## Summary

Implemented the foundation for ForgeMind Local — a standalone developer workstation companion. Provides YAML-based per-repo configuration, automatic git repo detection, and a `.forgemind/` directory structure for all local state.

## Deliverables

### Config (`apps/local/forgemind_local/config.py` — 131 lines)

- **`LocalConfig`** — dataclass with 8 fields: workspace_id, workspace_slug, project_slug, repo_root, mode, execution_policy, created_at, updated_at
- **`detect_repo_root()`** — walks up directory tree to find `.git/`; returns None if not in a repo
- **`load_config()` / `save_config()`** — YAML round-trip to `.forgemind/config.yaml`
- **`ensure_directories()`** — creates 5 subdirs: state, cache, index, patches, snapshots

### CLI (`apps/local/forgemind_local/cli.py` — init + status commands)

- **`forgemind init`** — creates `.forgemind/` workspace, saves config, prints success
- **`forgemind status`** — prints health table with workspace ID, mode, policy, file counts

### Package Config (`apps/local/pyproject.toml`)

- Package: `forgemind-local` v0.1.0
- Entry point: `forgemind = forgemind_local.cli:main`
- Deps: click, rich, pyyaml, gitpython, watchdog

## Tests

7 tests in `TestConfig`:
- default_config_fields, save_and_load_roundtrip, load_missing_returns_none, ensure_directories, detect_repo_root (positive + negative), to_dict_and_from_dict

## Test Results

- **Total**: 535 passing (482 backend + 53 local)
