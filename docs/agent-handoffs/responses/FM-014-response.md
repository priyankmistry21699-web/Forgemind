# FM-014 Response — Run & Task Display

## Status: COMPLETE

## What Was Done

### 1. Task types (`types/task.ts`)

- `TaskStatus` — union of 7 states: pending, blocked, ready, running, completed, failed, skipped
- `Task` — full interface matching backend `TaskRead` schema
- `TaskList` — `{ items, total }`

### 2. `fetchTasksByRun()` API function (`lib/tasks.ts`)

- GET /runs/{runId}/tasks → `TaskList`

### 3. `RunTaskList` component (`components/tasks/run-task-list.tsx`)

- Fetches and displays all tasks for a given run ID
- Color-coded status badges with dot indicators for each of 7 task states
- Visual highlighting: ready tasks have indigo background, blocked tasks have amber tint
- Shows order index, title, description, task type, dependency count
- Summary bar with total tasks, ready count, completed count
- Loading skeleton (3 animated rows)
- Error state with red banner
- Empty state message

### 4. Dashboard integration

- When a planning result exists, shows "Tasks — Latest Run" section with `RunTaskList`
- Task list and planning result are grouped together visually

## Files Created

- `apps/web/types/task.ts`
- `apps/web/lib/tasks.ts`
- `apps/web/components/tasks/run-task-list.tsx`

## Files Changed

- `apps/web/app/dashboard/page.tsx` — added RunTaskList import and conditional rendering

## API Endpoints Used

- `GET /runs/{run_id}/tasks` → `{ items: Task[], total: number }`
