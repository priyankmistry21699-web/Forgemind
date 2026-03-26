# ForgeMind Web

> Next.js 15 frontend for the ForgeMind platform.

## Overview

This is the web dashboard that provides:

- Project creation and management — **implemented**
- Prompt-to-plan intake with task generation — **implemented**
- Run and task display with status visualization — **implemented**
- Real-time agent monitoring — _planned_
- Code editor (Monaco) — _planned_
- Task DAG visualization (React Flow) — _planned_
- Connector setup wizard — _planned_
- Trust dashboard and drift scorecards — _planned_
- Replay viewer — _planned_
- Cost and analytics dashboards — _planned_

## Project Structure

```
apps/web/
├── package.json
├── tsconfig.json
├── next.config.mjs
├── postcss.config.mjs
├── .env.example               # Environment variable template
├── app/
│   ├── globals.css            # Global styles + CSS variables + Tailwind
│   ├── layout.tsx             # Root layout (html/body, metadata)
│   ├── page.tsx               # Landing / home page
│   └── dashboard/
│       ├── layout.tsx         # Dashboard shell (sidebar + top nav)
│       └── page.tsx           # Dashboard overview + project list + forms
├── components/
│   ├── layout/
│   │   ├── app-shell.tsx      # Sidebar + TopNav + content wrapper
│   │   ├── sidebar.tsx        # Left navigation
│   │   └── top-nav.tsx        # Top header bar
│   ├── planner/
│   │   ├── prompt-intake-form.tsx   # Prompt-to-plan form
│   │   └── planning-result-card.tsx # Planning success summary
│   ├── projects/
│   │   ├── project-create-form.tsx  # New project form
│   │   └── project-list.tsx   # ProjectCard, Empty, Skeleton, Error
│   └── tasks/
│       └── run-task-list.tsx  # Task list for a run with status badges
├── lib/
│   ├── api.ts                 # Fetch wrapper + ApiError class
│   ├── planner.ts             # Planner API functions
│   ├── projects.ts            # Project API functions
│   └── tasks.ts               # Task API functions
├── types/
│   ├── planner.ts             # Planner TypeScript interfaces
│   ├── project.ts             # Project TypeScript interfaces
│   └── task.ts                # Task TypeScript interfaces
└── README.md
```

## Tech Stack

- **Next.js 15** (App Router, Server Components)
- **TypeScript 5.x**
- **Tailwind CSS 4** (via `@tailwindcss/postcss`)
- **React 19**

Future additions (not installed yet):

- shadcn/ui, Zustand, React Query, Socket.IO Client
- Monaco Editor, Mermaid.js, React Flow, Recharts

## Development

### Via Docker Compose (recommended)

```bash
# From repo root — starts Web + API + all dependencies
docker compose up -d web

# Tail logs
docker compose logs -f web
```

### Locally (without Docker)

```bash
# From repo root
make install-web
make dev-web

# Or manually
cd apps/web
npm install
npm run dev
```

Visit `http://localhost:3000` once running.

## Routes

| Path         | Description                               |
| ------------ | ----------------------------------------- |
| `/`          | Landing page — explains what ForgeMind is |
| `/dashboard` | Dashboard overview with live project list |

## Environment Variables

| Variable              | Default                 | Description          |
| --------------------- | ----------------------- | -------------------- |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Backend API base URL |

Copy `.env.example` to `.env.local` for local development.

## Styling

- Dark theme by default using CSS custom properties in `globals.css`
- Tailwind CSS 4 for utility classes
- Color tokens: `--color-bg`, `--color-accent`, `--color-text-muted`, etc.
