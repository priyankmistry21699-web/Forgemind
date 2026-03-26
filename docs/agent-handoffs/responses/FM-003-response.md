TASK ID:
FM-003

STATUS:
done

SUMMARY:
Created the Next.js 15 frontend shell with App Router, Tailwind CSS 4, a landing page, dashboard route with app shell layout (sidebar + top nav), and dark theme styling. The app is structured for clean expansion with future auth/project pages slotting in naturally.

FILES CHANGED:

- apps/web/package.json
- apps/web/tsconfig.json
- apps/web/next.config.mjs
- apps/web/postcss.config.mjs
- apps/web/app/globals.css
- apps/web/app/layout.tsx
- apps/web/app/page.tsx
- apps/web/app/dashboard/layout.tsx
- apps/web/app/dashboard/page.tsx
- apps/web/components/layout/app-shell.tsx
- apps/web/components/layout/sidebar.tsx
- apps/web/components/layout/top-nav.tsx
- apps/web/README.md (updated)

IMPLEMENTATION NOTES:

- Tailwind CSS 4 configured via @tailwindcss/postcss (new PostCSS plugin approach, not tailwind.config.js)
- Dark theme using CSS custom properties (--color-bg, --color-accent, etc.) for consistency and future theming
- Landing page (/) is a standalone page without the app shell — clean hero with feature highlights
- Dashboard (/dashboard) uses a nested layout that wraps children in AppShell (sidebar + top nav)
- Sidebar has nav items: Dashboard (active), Projects/Agents/Connectors/Settings (disabled with "soon" label)
- Dashboard page has: stats cards (4), quick actions (disabled), and recent activity placeholder
- All future app pages behind /dashboard will automatically get the sidebar+nav layout
- React 19 + Next.js 15 with App Router — no pages/ directory
- tsconfig paths set up: @/\* maps to project root

ASSUMPTIONS:

- npm install must be run before dev server starts (not done automatically)
- No shadcn/ui installed yet — will add when UI complexity warrants it (FM-012+)
- No API calls — all data is static placeholder
- The Inter font is expected to be available via system fonts (no @next/font added to keep it minimal)

BLOCKERS:

- None

NEXT RECOMMENDED STEP:

- FM-004: Add Docker Compose with Postgres and Redis (already partially done — may need app service definitions)
