TASK ID:
FM-011

STATUS:
done

SUMMARY:
Created a frontend API integration layer and connected the dashboard to the backend project list endpoint. The dashboard now fetches real project data with loading, error, and empty states. Added TypeScript types, a reusable API client, project data functions, and project display components.

FILES CHANGED:

- apps/web/types/project.ts (created — Project, ProjectStatus, ProjectList interfaces)
- apps/web/lib/api.ts (created — apiFetch wrapper + ApiError class)
- apps/web/lib/projects.ts (created — fetchProjects function)
- apps/web/components/projects/project-list.tsx (created — ProjectCard, ProjectListEmpty, ProjectListSkeleton, ProjectListError)
- apps/web/app/dashboard/page.tsx (updated — client component with useEffect data fetching, live project grid)
- apps/web/.env.example (created — NEXT_PUBLIC_API_URL)
- apps/web/README.md (updated — project structure, env vars table, route descriptions)

IMPLEMENTATION NOTES:

- API client uses a thin `apiFetch<T>()` generic wrapper over native `fetch` — no external deps
- `ApiError` class captures status, statusText, and response body for structured error handling
- `NEXT_PUBLIC_API_URL` is the only env var; defaults to http://localhost:8000 for local dev
- Dashboard page converted from server component to client component (`"use client"`) for interactive state management
- Data fetching uses `useEffect` + `useState` — deliberately simple, no React Query yet (per handoff scope)
- `useEffect` cleanup prevents state updates on unmounted components (race condition guard)
- Project card shows name, description (2-line clamp), status badge (color-coded per status), and relative time
- Four display states: loading skeleton (3 animated cards), error (red banner with message), empty (dashed border CTA), populated grid
- Stats row now shows live project count from API response total
- Status badge colors: draft=zinc, planning=indigo, active=emerald, paused=amber, completed=green, failed=red
- All components are in a `components/projects/` directory ready for FM-012 additions

ASSUMPTIONS:

- Backend is running at localhost:8000 (via Docker Compose or `make dev-api`)
- CORS is already configured on the backend to allow requests from localhost:3000
- No auth headers needed yet (backend uses stub owner)
- Project list is adequate at 20-item default limit for MVP

BLOCKERS:

- None

NEXT RECOMMENDED STEP:

- FM-012: Project creation UI (form/modal on dashboard)
