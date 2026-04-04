# FM-099 — Handoff Snapshots

## Summary

Implemented export/import of workspace snapshot bundles for team handoff and machine migration. Bundles are timestamped zip files containing config, manifest, patches metadata, sync queue, run logs, and a bundle manifest.

## Deliverables

### Service (`apps/local/forgemind_local/local_handoff.py` — 188 lines)

- **`export_snapshot(repo_root, output_path=None)`** — creates zip bundle containing:
  - `config.yaml` — workspace configuration
  - `index/repo_manifest.json` — cached repo index
  - `patches/*.json` — patch metadata (not diff files, for safety)
  - `sync_queue/` — last 50 sync events
  - `runs/` — last 20 run logs
  - `pr_summary.md` — most recent PR materials
  - `manifest.json` — bundle metadata (bundle_id, exported_at, workspace_slug, contents)

- **`import_snapshot(bundle_path, repo_root)`** — unpacks bundle into `.forgemind/`:
  - **Non-destructive** — will not overwrite existing `config.yaml`
  - Copies index, patches, and run logs
  - Returns the bundle manifest dict

- **`inspect_bundle(bundle_path)`** — reads manifest without importing (preview only)

### CLI

- **`forgemind snapshot export`** — creates zip in `.forgemind/snapshots/`
- **`forgemind snapshot import <path>`** — imports bundle into workspace

## Design Notes

- Patches are exported as metadata-only (JSON), not raw diff files — this prevents accidental code leakage
- Import is deliberately non-destructive to prevent overwriting active workspace state
- Uses `shutil.unpack_archive` for zip extraction

## Tests

5 tests in `TestLocalHandoff`:
- export_creates_zip, export_import_roundtrip, inspect_bundle, import_missing_raises, import_does_not_overwrite_existing_config

## Test Results

- **Total**: 535 passing
