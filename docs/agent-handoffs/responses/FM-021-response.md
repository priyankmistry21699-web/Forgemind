# FM-021 Response — Execution Artifact Model and Persistence

**Status:** Complete
**Date:** 2026-03-26

---

## Summary

FM-021 introduces a first-class `Artifact` model for storing outputs produced by tasks and agents. This is the foundational storage layer that execution agents (FM-025) will write their work products into.

---

## Files Created

| File                                                              | Purpose                                                                            |
| ----------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| `apps/api/app/models/artifact.py`                                 | Artifact SQLAlchemy model with ArtifactType enum                                   |
| `apps/api/app/schemas/artifact.py`                                | ArtifactRead, ArtifactList, ArtifactCreate, ArtifactUpdate Pydantic schemas        |
| `apps/api/app/services/artifact_service.py`                       | CRUD service: create, get, list (with filters), update (with version bump), delete |
| `apps/api/app/api/routes/artifacts.py`                            | REST endpoints: POST/GET list/GET single/PATCH/DELETE                              |
| `apps/api/alembic/versions/2026_03_26_0002_0003_add_artifacts.py` | Migration: artifacts table + artifact_type enum                                    |

## Files Modified

| File                             | Change                                            |
| -------------------------------- | ------------------------------------------------- |
| `apps/api/app/models/project.py` | Added `artifacts` relationship (cascade delete)   |
| `apps/api/app/models/run.py`     | Added `artifacts` relationship                    |
| `apps/api/app/models/task.py`    | Added `artifacts` relationship                    |
| `apps/api/app/db/base.py`        | Added `Artifact` import for Alembic metadata      |
| `apps/api/app/api/router.py`     | Mounted artifacts router with `["artifacts"]` tag |

---

## Artifact Model Design

### Fields

- `id` — UUID primary key
- `title` — String(500), required
- `artifact_type` — Enum: plan_summary, architecture, implementation, review, test_report, documentation, other
- `content` — Text, the actual artifact body
- `meta` — JSON, optional metadata (structured key-value)
- `version` — Integer, auto-bumped on content updates
- `project_id` — FK to projects (CASCADE delete), required
- `run_id` — FK to runs (SET NULL on delete), optional
- `task_id` — FK to tasks (SET NULL on delete), optional
- `created_by` — String(100), tracks which agent/user created it
- `created_at`, `updated_at` — timestamps

### Relationships

- `Artifact.project` ↔ `Project.artifacts` (cascade delete)
- `Artifact.run` ↔ `Run.artifacts`
- `Artifact.task` ↔ `Task.artifacts`

---

## API Endpoints

| Method | Path                               | Description                                           |
| ------ | ---------------------------------- | ----------------------------------------------------- |
| POST   | `/projects/{project_id}/artifacts` | Create artifact                                       |
| GET    | `/projects/{project_id}/artifacts` | List artifacts (filter by run_id, task_id; paginated) |
| GET    | `/artifacts/{artifact_id}`         | Get single artifact                                   |
| PATCH  | `/artifacts/{artifact_id}`         | Update artifact (bumps version on content change)     |
| DELETE | `/artifacts/{artifact_id}`         | Delete artifact                                       |

---

## Design Decisions

1. **Artifact belongs to project, optionally to run/task** — This allows artifacts at any scope (project-level docs, run-level summaries, task-level outputs)
2. **Version field with auto-bump** — When `content` changes via update, version increments. Simple versioning without full history (TD candidate for later)
3. **`created_by` as string, not FK** — Agents don't have user accounts yet (FM-022 will introduce agent registry). String is flexible enough to store "planner", "coder-agent", or a user UUID later
4. **SET NULL on run/task delete** — Artifacts survive if a run or task is deleted, preserving audit trail
5. **CASCADE on project delete** — Artifacts are owned by the project; deleting the project cleans everything

---

## Ready for FM-022

The artifact layer is now in place. Execution agents (FM-025) will create artifacts via `artifact_service.create_artifact()`. The agent registry (FM-022) will define which agents are allowed to produce which artifact types.
