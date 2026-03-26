TASK ID:
FM-007

STATUS:
done

SUMMARY:
Created four core SQLAlchemy models — User, Project, Run, Task — with UUID primary keys, timezone-aware timestamps (server_default=func.now()), status enums, foreign keys with cascade deletes, and bidirectional relationships. All models are imported in db/base.py so Alembic's target_metadata is fully populated.

FILES CHANGED:

- apps/api/app/models/**init**.py (created — re-exports all models and enums)
- apps/api/app/models/user.py (created — User model with email, clerk_id, is_active)
- apps/api/app/models/project.py (created — Project model with ProjectStatus enum, owner FK)
- apps/api/app/models/run.py (created — Run model with RunStatus enum, run_number, trigger)
- apps/api/app/models/task.py (created — Task with TaskStatus enum, DAG depends_on ARRAY, parent_id self-FK)
- apps/api/app/db/base.py (updated — imports all 4 models for metadata population)

IMPLEMENTATION NOTES:

- UUID columns use sqlalchemy.dialects.postgresql.UUID(as_uuid=True) for native PostgreSQL UUID support
- Status enums are Python str enums (serializable) stored as Postgres ENUM types
- User.email has unique+index; User.clerk_id has unique+index (nullable until Clerk is wired)
- Project.status indexed for efficient filtering
- Run.run_number is per-project sequence (not globally unique)
- Task.depends_on uses PostgreSQL ARRAY(UUID) for lightweight DAG — stores IDs of prerequisite tasks
- Task.parent_id is a self-referential FK (ondelete=SET NULL) for parent-child subtask grouping
- All relationships use cascade="all, delete-orphan" for proper cleanup
- onupdate=func.now() on updated_at columns for automatic timestamp tracking

ASSUMPTIONS:

- PostgreSQL ARRAY type is acceptable for dependency tracking (vs. a junction table)
- Status enums will grow over time — current values cover the core lifecycle
- clerk_id is nullable because auth is not yet wired
- No indexes on created_at yet — can be added when query patterns emerge

BLOCKERS:

- None

NEXT RECOMMENDED STEP:

- FM-008: Project CRUD API endpoints
