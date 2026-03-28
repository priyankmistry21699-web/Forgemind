# FM-048 — Multi-Run Memory & Project Knowledge Base

## What was done

Created a project-scoped knowledge base that captures patterns, decisions, lessons learned, and best practices from completed runs, enabling cross-run learning and agent enrichment with project context.

## Files created

- `apps/api/app/models/project_knowledge.py` — `ProjectKnowledge` model:
  - `KnowledgeType` enum: `PATTERN`, `DECISION`, `LESSON_LEARNED`, `DEPENDENCY`, `BEST_PRACTICE`, `ARCHITECTURE`, `CONSTRAINT`
  - FK to project (CASCADE), `source_run_id`/`source_task_id` (SET NULL) for provenance
  - `title`, `content`, `tags` (JSON), `metadata_` (JSON)
  - `relevance_score` (float, default 1.0), `usage_count` (int, default 0)
- `apps/api/app/services/knowledge_service.py` — Knowledge service:
  - `create_knowledge()`, `get_knowledge()`, `list_knowledge()`: CRUD with type/tag filters, ordered by relevance descending
  - `extract_knowledge_from_run(db, run_id)`: Automated extraction from completed runs — analyzes tasks, artifacts, planner results to generate knowledge entries
  - Knowledge context assembly for agent enrichment (text summary of project learnings)
- `apps/api/app/api/routes/knowledge.py` — Routes: `POST /projects/{id}/knowledge`, `GET /projects/{id}/knowledge`, `GET /knowledge/{id}`, `POST /runs/{id}/knowledge/extract`, `GET /projects/{id}/knowledge/context`
- `apps/api/app/schemas/knowledge.py` — Read/create schemas
- `apps/api/alembic/versions/2026_03_30_0017_add_project_knowledge.py` — Migration creating `project_knowledge`

## Files modified

- `apps/api/app/db/base.py` — Added `ProjectKnowledge` import
- `apps/api/app/api/router.py` — Registered `knowledge_router`

## Design decisions

- Knowledge is project-scoped with run/task provenance tracking
- Relevance scoring + usage counting enables future knowledge ranking and deprecation
- Automated extraction creates structured knowledge from raw execution data
- `knowledge/context` endpoint produces text summaries agents can consume directly
