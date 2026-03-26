# FM-012 Response — Project Creation UI

## Status: COMPLETE

## What Was Done

### 1. `createProject()` API function (`lib/projects.ts`)

- Added `createProject(data: { name: string; description?: string | null })` → POST /projects
- Returns the created `Project` object

### 2. `ProjectCreateForm` component (`components/projects/project-create-form.tsx`)

- Form with name (required, max 255 chars) and description (optional, max 2000 chars) fields
- Submit/Cancel buttons with loading state ("Creating…")
- Error display on failure
- Calls `onCreated()` callback on success to refresh project list
- Calls `onCancel()` to dismiss the form

### 3. Dashboard integration (`app/dashboard/page.tsx`)

- "+ New Project" button in page header opens the form inline
- Form and project list refresh are wired together via `loadProjects()` callback
- "New Project" in Quick Actions also triggers the form

## Files Changed

- `apps/web/lib/projects.ts` — added `createProject()` export
- `apps/web/components/projects/project-create-form.tsx` — **new file**
- `apps/web/app/dashboard/page.tsx` — refactored to use `loadProjects` callback, added form toggle

## API Endpoints Used

- `POST /projects` — creates a project with `{ name, description }`

## Testing Notes

- Requires backend running with POST /projects endpoint available
- Form validation: name is required (HTML5 + trim check), submit disabled when empty or submitting
