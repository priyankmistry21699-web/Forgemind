TASK ID:
FM-008

STATUS:
done

SUMMARY:
Implemented full Project CRUD with Pydantic schemas (ProjectCreate, ProjectUpdate, ProjectRead, ProjectList), a service layer with proper pagination (offset/limit + total count), and four FastAPI endpoints (POST, GET list, GET by ID, PATCH). Uses a temporary hardcoded owner_id until Clerk auth is wired.

FILES CHANGED:

- apps/api/app/schemas/**init**.py (created)
- apps/api/app/schemas/project.py (created — ProjectCreate, ProjectUpdate, ProjectRead, ProjectList)
- apps/api/app/services/**init**.py (created)
- apps/api/app/services/project_service.py (created — create, get, list, update functions)
- apps/api/app/api/routes/projects.py (created — POST/GET/GET:id/PATCH endpoints)
- apps/api/app/api/router.py (updated — registered projects_router)
- apps/api/README.md (updated — endpoint table)

IMPLEMENTATION NOTES:

- Schemas use from_attributes=True for SQLAlchemy → Pydantic conversion
- ProjectUpdate uses model_dump(exclude_unset=True) for partial updates (PATCH semantics)
- Pagination: skip/limit query params with sensible defaults (0/20) and max limit=100
- Total count uses subquery count for accuracy with filters
- Service layer is pure async functions (not a class) — simple and testable
- TEMP_OWNER_ID placeholder (UUID 0...01) will be replaced by Clerk JWT extraction
- 404 raised via HTTPException in the service layer for missing projects

ASSUMPTIONS:

- No DELETE endpoint yet — can be added when soft-delete strategy is decided
- Owner filtering is applied to list but not to get/update (assumes frontend authorization)
- Project name min_length=1 prevents empty names; max_length=255 matches DB column

BLOCKERS:

- None

NEXT RECOMMENDED STEP:

- FM-009: Prompt intake + planner stub
