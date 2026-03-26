# FM-016 Response — Project Detail Page with Runs/Tasks View

## Status: COMPLETE

---

## Files Created

| File                                                   | Purpose                                                                    |
| ------------------------------------------------------ | -------------------------------------------------------------------------- |
| `apps/api/app/schemas/run.py`                          | `RunRead` and `RunList` Pydantic schemas                                   |
| `apps/api/app/api/routes/runs.py`                      | `GET /projects/{id}/runs` (paginated) and `GET /projects/{id}/runs/latest` |
| `apps/web/types/run.ts`                                | `RunStatus`, `Run`, `RunList` TypeScript interfaces                        |
| `apps/web/app/dashboard/projects/[projectId]/page.tsx` | Project detail page component                                              |

## Files Modified

| File                                            | Change                                                                           |
| ----------------------------------------------- | -------------------------------------------------------------------------------- |
| `apps/api/app/api/router.py`                    | Registered `runs_router` with prefix `/projects`                                 |
| `apps/web/lib/projects.ts`                      | Added `fetchProject()` and `fetchLatestRun()` functions                          |
| `apps/web/components/projects/project-list.tsx` | `ProjectCard` now wraps content in `<Link>` to `/dashboard/projects/[projectId]` |

---

## Backend

### Run Schemas (`app/schemas/run.py`)

- `RunRead`: id, run_number, status, trigger, project_id, created_at, updated_at
- `RunList`: items (list of RunRead), total count

### Run Routes (`app/api/routes/runs.py`)

- `GET /projects/{project_id}/runs` — paginated list, newest first (by created_at desc)
- `GET /projects/{project_id}/runs/latest` — returns the most recent run or 404

---

## Frontend

### Project Detail Page

- Dynamic route at `/dashboard/projects/[projectId]`
- Fetches project + latest run in parallel on mount
- Displays: breadcrumb nav, project header with status badge, metadata cards (status, created, updated), latest run summary with status badge, task list via `RunTaskList` component
- Handles: loading skeleton, error state, no-runs empty state

### ProjectCard Navigation

- Each `ProjectCard` in the dashboard list is now a `<Link>` to the detail page
- Clicking a project card navigates to `/dashboard/projects/{id}`

### API Functions

- `fetchProject(projectId)` → `GET /projects/{id}`
- `fetchLatestRun(projectId)` → `GET /projects/{id}/runs/latest` (returns null on 404)

---

## UI States

| State             | Display                                         |
| ----------------- | ----------------------------------------------- |
| Loading           | Pulse animation skeleton with placeholder cards |
| Error / Not found | Red error banner with "Back to Dashboard" link  |
| No runs           | Dashed border empty state with guidance text    |
| Has run           | Run summary card + full task list               |

---

## Technical Debt: None introduced
