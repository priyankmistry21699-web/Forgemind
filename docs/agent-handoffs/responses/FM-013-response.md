# FM-013 Response — Prompt Intake UI

## Status: COMPLETE

## What Was Done

### 1. Planner types (`types/planner.ts`)

- `PromptIntakeRequest` — `{ prompt, project_name? }`
- `PromptIntakeResponse` — `{ project_id, run_id, tasks_created, message, created_at }`

### 2. `submitPromptIntake()` API function (`lib/planner.ts`)

- POST /planner/intake with prompt text and optional project name
- Returns `PromptIntakeResponse`

### 3. `PromptIntakeForm` component (`components/planner/prompt-intake-form.tsx`)

- Textarea for prompt (required, min 10 chars, max 5000) with character counter
- Optional project name field
- Submit/Cancel with loading state ("Planning…")
- Error display on failure
- Calls `onPlanned(result)` with the response on success

### 4. `PlanningResultCard` component (`components/planner/planning-result-card.tsx`)

- Success banner showing task count, truncated project/run IDs
- Dismiss button to clear the result

### 5. Dashboard integration

- "Plan from Prompt" button in header and Quick Actions opens the form
- On success: shows PlanningResultCard, refreshes project list
- Forms are mutually exclusive (only one open at a time via `activeForm` state)

## Files Created

- `apps/web/types/planner.ts`
- `apps/web/lib/planner.ts`
- `apps/web/components/planner/prompt-intake-form.tsx`
- `apps/web/components/planner/planning-result-card.tsx`

## Files Changed

- `apps/web/app/dashboard/page.tsx` — added prompt intake imports and form toggle

## API Endpoints Used

- `POST /planner/intake` — `{ prompt, project_name? }` → `{ project_id, run_id, tasks_created, message, created_at }`
