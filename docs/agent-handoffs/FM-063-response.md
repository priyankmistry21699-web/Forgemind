# FM-063 — Code Artifact Mapping

## What was done

Extended the Artifact model to link artifacts to specific repository files, enabling traceability from planning artifacts to the code files they describe or generate.

## Files modified

- `apps/api/app/models/artifact.py` — Added `ChangeType` enum (CREATE, MODIFY, DELETE, CONCEPTUAL). Added 5 new columns: `repo_connection_id` (FK to repo_connections, nullable), `target_path` (file path in repo), `target_module` (module/package name), `change_type` (ChangeType enum), `target_metadata` (JSON for extra mapping data).
- `apps/api/app/schemas/artifact.py` — Added all 5 new fields to `ArtifactRead`, `ArtifactCreate`, `ArtifactUpdate` schemas with appropriate Optional typing.
- `apps/api/app/services/artifact_service.py` — Updated `create_artifact()` to pass FM-063 fields (repo_connection_id, target_path, target_module, change_type, target_metadata).
- `apps/api/alembic/versions/2026_03_31_0021_add_code_ops_enhancements.py` — Adds columns to artifacts table.

## Design decisions

- `ChangeType.CONCEPTUAL` for artifacts that describe architectural decisions rather than concrete file changes
- `repo_connection_id` is nullable — artifacts can exist without repo links (backward compatible)
- `target_metadata` JSON column for flexibility: stores line ranges, function names, class names, or any provider-specific mapping info
- FK to `repo_connections` (not `code_mappings`) because artifacts may reference files in repos that don't have CodeMapping entries yet
