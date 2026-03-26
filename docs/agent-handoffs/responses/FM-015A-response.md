# FM-015A Response — Frontend Validation Pass

## Status: COMPLETE

---

## 1. Type Alignment Validation

All frontend types were cross-referenced against backend Pydantic schemas and SQLAlchemy models.

| Frontend Type                     | Backend Schema         | Result                                                                                                                                          |
| --------------------------------- | ---------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| `Project` (7 fields)              | `ProjectRead`          | **Match** — `id`, `name`, `description`, `status`, `owner_id`, `created_at`, `updated_at`                                                       |
| `ProjectStatus` (6 values)        | `ProjectStatus` enum   | **Match** — `draft`, `planning`, `active`, `paused`, `completed`, `failed` (backend uses lowercase via `str, enum.Enum`)                        |
| `PromptIntakeRequest`             | `PromptIntakeRequest`  | **Match** — `prompt`, `project_name`                                                                                                            |
| `PromptIntakeResponse` (5 fields) | `PromptIntakeResponse` | **Match** — `project_id`, `run_id`, `tasks_created`, `message`, `created_at`                                                                    |
| `Task` (11 fields)                | `TaskRead`             | **Match** — `id`, `title`, `description`, `task_type`, `status`, `order_index`, `depends_on`, `parent_id`, `run_id`, `created_at`, `updated_at` |
| `TaskStatus` (7 values)           | `TaskStatus` enum      | **Match** — `pending`, `blocked`, `ready`, `running`, `completed`, `failed`, `skipped`                                                          |

**No field naming mismatches found.** Backend uses `snake_case` throughout; frontend types mirror exactly.

---

## 2. Dashboard State Flow Validation

### Scenario 1 — Create project → list refresh

- `ProjectCreateForm.onCreated` → calls `setActiveForm("none")` + `loadProjects()`
- **Result: Correct.** Form closes, project list re-fetches and displays the new project.

### Scenario 2 — Submit prompt → result + tasks + list refresh

- `PromptIntakeForm.onPlanned(result)` → sets `planningResult`, closes form, re-fetches projects
- `PlanningResultCard` renders with project_id, run_id, tasks_created
- `RunTaskList` fetches tasks from `/runs/{run_id}/tasks`
- **Result: Correct.** All three sections appear coherently.

### Scenario 3 — Switch between forms

- `openForm()` uses single `activeForm` state — only one form can be open at a time
- Toggling header buttons opens/closes the active form
- **Result: Correct.** No leftover state or visual conflict.

### Scenario 4 — Planner request fails

- **Issue found:** If user had a prior successful planning result visible, then opened prompt form again to retry, the old planning result and task list would remain visible below the form. This is confusing.
- **Fix applied:** `openForm("prompt")` now clears `planningResult` to null, removing stale result/tasks when the user starts a new planning attempt.

### Scenario 5 — Task fetch fails independently

- `RunTaskList` has its own error state (red banner: "Failed to load tasks")
- `PlanningResultCard` remains visible above the error
- **Result: Correct.** Planning result is preserved; task section shows useful error.

---

## 3. Issues Found and Fixed

### Issue 1: Stale planning result when re-opening prompt form

- **Problem:** After a successful plan, clicking "Plan from Prompt" again would show the new form while the old PlanningResultCard + RunTaskList remained visible below it, creating visual confusion.
- **Fix:** `openForm("prompt")` now calls `setPlanningResult(null)` to clear prior results.
- **File:** `apps/web/app/dashboard/page.tsx`

### Issue 2: Quick Actions don't scroll to form

- **Problem:** Clicking "New Project" or "Plan from Prompt" in the Quick Actions section (at the bottom of the page) opens the form above the Projects section, but the user's viewport stays at the bottom — they don't see the form appear.
- **Fix:** Added `formRef` on the form container div. The `openForm()` helper scrolls it into view with `scrollIntoView({ behavior: "smooth", block: "nearest" })` after a tick.
- **File:** `apps/web/app/dashboard/page.tsx`

### Issue 3: Duplicate form-toggle logic

- **Problem:** Header buttons and Quick Actions buttons used separate inline `setActiveForm` calls — easy to diverge in behavior.
- **Fix:** Extracted `openForm()` callback that centralizes form-opening logic (state change + result clearing + scroll). Both header and Quick Actions now use it.
- **File:** `apps/web/app/dashboard/page.tsx`

---

## 4. Things Validated as Correct (No Change Needed)

- **API client (`lib/api.ts`):** Content-Type header, error parsing, ApiError class — all correct
- **Form validation:** Both forms validate input before submit (project name trim check, prompt min 10 chars)
- **Loading states:** All three data-fetching flows (projects, planner, tasks) have loading indicators
- **Error states:** All three handle errors with user-visible messages
- **Empty states:** ProjectListEmpty and RunTaskList empty state both present
- **RunTaskList cleanup:** Uses `cancelled` flag pattern for proper effect cleanup
- **Status badge mappings:** Both `ProjectStatus` (6 values) and `TaskStatus` (7 values) have complete style maps with fallbacks

---

## 5. TypeScript Errors Note

VS Code reports "Cannot find module 'react'" errors in `dashboard/page.tsx`. These are **environment-only** — `node_modules` is not installed in the workspace. All other files (11 of 11) report zero errors. The code is structurally sound; errors will resolve after `npm install`.

---

## 6. Remaining Technical Debt / Assumptions

| Item                                   | Severity | Notes                                                                                                                         |
| -------------------------------------- | -------- | ----------------------------------------------------------------------------------------------------------------------------- |
| Task display only from planning result | Low      | Tasks are only visible when `planningResult` is set. Later, a project detail view should fetch tasks by selected project/run. |
| Dashboard page growing                 | Low      | ~190 lines. Not critical yet, but should split into sub-panels when adding more features.                                     |
| No cancellation on `loadProjects`      | Low      | React 19 handles this gracefully (no unmount warnings), acceptable for MVP.                                                   |
| Forms reset on re-mount                | Info     | Form state clears when toggled off/on — this is the desired behavior (no stale input).                                        |

---

## Files Changed

- `apps/web/app/dashboard/page.tsx` — 3 targeted fixes (stale result clear, scroll-to-form, centralized `openForm`)

## Files Validated (No Changes)

- `apps/web/components/projects/project-create-form.tsx`
- `apps/web/components/projects/project-list.tsx`
- `apps/web/components/planner/prompt-intake-form.tsx`
- `apps/web/components/planner/planning-result-card.tsx`
- `apps/web/components/tasks/run-task-list.tsx`
- `apps/web/lib/api.ts`
- `apps/web/lib/projects.ts`
- `apps/web/lib/planner.ts`
- `apps/web/lib/tasks.ts`
- `apps/web/types/project.ts`
- `apps/web/types/planner.ts`
- `apps/web/types/task.ts`
