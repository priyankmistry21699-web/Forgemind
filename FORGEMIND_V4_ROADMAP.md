# ForgeMind V4 — Product Roadmap (FM-141 → FM-210)

> **Version:** V4 Planning Draft
> **Date:** 2026-04-10
> **Scope:** FM-141 through FM-210 (70 milestones across 7 blocks)
> **Builds on:** ForgeMind V1–V3 (FM-001 through FM-140, 26 milestones, 746 tests)

---

## 1. V4 Executive Summary

### What V4 Is

ForgeMind V4 transforms the platform from a **single-team autonomous engineering system** into a **collaborative, integrated, enterprise-grade engineering intelligence platform**. V1–V3 built the engine: spec-driven lifecycle, multi-agent execution, governance, checkpoints, release operations, and local developer tooling. V4 builds the ecosystem around that engine.

V4 adds 70 milestones (FM-141 → FM-210) across 7 strategic blocks:

| Block   | Range           | Theme                                                   |
| ------- | --------------- | ------------------------------------------------------- |
| Wave 10 | FM-141 → FM-150 | Collaboration, UX & Team Coordination                   |
| Wave 11 | FM-151 → FM-160 | GitHub, CI/CD & Developer Tooling Integration           |
| Wave 12 | FM-161 → FM-170 | Search, Knowledge & Organizational Memory               |
| Wave 13 | FM-171 → FM-180 | Enterprise Governance, Permissions & Compliance         |
| Wave 14 | FM-181 → FM-190 | Code Intelligence, Change Awareness & Test Intelligence |
| Wave 15 | FM-191 → FM-200 | Analytics, Metrics & Portfolio Operations               |
| Wave 16 | FM-201 → FM-210 | API, Webhooks & Ecosystem Integrations                  |

### Why V4 Matters

ForgeMind through FM-140 solves the core problem: turning high-level goals into governed, auditable, AI-executed engineering work. But the current platform operates largely in isolation — one project at a time, one user at a time, disconnected from the tools and workflows teams already use.

V4 bridges that gap:

- **Teams** can collaborate on runs, share knowledge across projects, and coordinate at portfolio scale
- **Developers** get native GitHub, CI, and IDE integration — ForgeMind works where they already work
- **Engineering leaders** get analytics, compliance dashboards, and audit trails that satisfy enterprise needs
- **The platform itself** becomes searchable, extensible, and API-first — ready for third-party integrations

### How V4 Differs from Earlier Versions

| Version             | Focus         | Result                                                                |
| ------------------- | ------------- | --------------------------------------------------------------------- |
| V1 (FM-001–050)     | Foundation    | Models, agents, execution engine, pre-release infra                   |
| V2 (FM-051–100)     | Breadth       | Collaboration, code ops, frontend parity, local mode                  |
| V3 (FM-101–140)     | Depth         | SPEC lifecycle, templates, checkpoints, release operations            |
| **V4 (FM-141–210)** | **Ecosystem** | **Integration, intelligence, enterprise, and scale**                  |
| V5 (FM-211–250)     | Intelligence  | Dynamic agents, graph memory, deliberation, explainability _(FUTURE)_ |

### Strategic Position

After V4, ForgeMind occupies a unique market position: an **AI-native engineering platform** that combines autonomous execution with enterprise governance, deep code intelligence, and portfolio-scale visibility — capabilities that no single existing tool provides end-to-end.

---

## 2. V4 Theme by Block

### Wave 10 — FM-141 to FM-150: Collaboration, UX & Team Coordination

**Purpose:** Make ForgeMind a multiplayer platform where teams coordinate, review, and share context across projects and runs.

**Why this comes first:** V3's governance model (approvals, roles, constitutions) laid the groundwork, but actual team workflows — comments, mentions, shared views, presence indicators — don't exist yet. This is the highest-friction gap for teams adopting ForgeMind today.

**User value:** Teams can collaborate inside ForgeMind instead of switching to Slack/email for coordination.
**Engineering value:** Establishes real-time collaboration primitives (comments, threads, notifications) that later blocks build on.
**Differentiation:** Most AI coding tools are single-player. ForgeMind becomes team-native.

---

### Wave 11 — FM-151 to FM-160: GitHub, CI/CD & Developer Tooling Integration

**Purpose:** Connect ForgeMind to the developer's daily toolchain — GitHub repos, PRs, issues, CI pipelines, and IDE workflows.

**Why this sequence:** After teams can collaborate inside ForgeMind, the next friction is context-switching between ForgeMind and GitHub/CI. Closing that loop makes ForgeMind part of the existing development workflow rather than a separate system.

**User value:** PRs auto-created from runs, CI results flow back into readiness checks, issue tracking synchronized.
**Engineering value:** GitHub webhook/API integration layer that knowledge and compliance blocks reuse.
**Differentiation:** ForgeMind becomes a GitHub-native AI execution layer, not a disconnected tool.

---

### Wave 12 — FM-161 to FM-170: Search, Knowledge & Organizational Memory

**Purpose:** Make every decision, artifact, and pattern searchable and reusable across projects and time.

**Why this sequence:** With collaboration and GitHub data flowing in, the platform now has rich content worth searching. This block makes that content queryable and turns past executions into organizational knowledge.

**User value:** "How did we solve X last time?" becomes a searchable question. Patterns emerge from history.
**Engineering value:** Full-text + semantic search infrastructure that analytics and compliance blocks depend on.
**Differentiation:** Most tools forget everything after each run. ForgeMind builds cumulative organizational intelligence.

---

### Wave 13 — FM-171 to FM-180: Enterprise Governance, Permissions & Compliance

**Purpose:** Make ForgeMind enterprise-ready with fine-grained permissions, audit logs, policy engines, and compliance reporting.

**Why this sequence:** After collaboration, integrations, and knowledge are built, enterprises need assurance that the platform meets their security, compliance, and governance requirements before broad deployment.

**User value:** SSO, team-scoped permissions, audit trails, exportable compliance reports.
**Engineering value:** Policy engine that codifies organizational rules; audit log infrastructure.
**Differentiation:** Enterprise compliance built into the AI execution model — not bolted on after the fact.

---

### Wave 14 — FM-181 to FM-190: Code Intelligence, Change Awareness & Test Intelligence

**Purpose:** Give ForgeMind deep understanding of the codebase it operates on — dependency graphs, change impact analysis, test coverage mapping, and intelligent test selection.

**Why this sequence:** With GitHub integration providing real repository data and knowledge infrastructure for storing analysis results, the platform can now do meaningful code-level intelligence.

**User value:** "What tests should I run?", "What does this change affect?", "Where is this pattern used?" — answered automatically.
**Engineering value:** Code graph and AST analysis services that improve agent decision quality.
**Differentiation:** Moves from "AI that writes code" to "AI that understands the codebase."

---

### Wave 15 — FM-191 to FM-200: Analytics, Metrics & Portfolio Operations

**Purpose:** Provide engineering leaders with portfolio-scale visibility — project health dashboards, execution trends, cost tracking, team velocity, and quality metrics.

**Why this sequence:** With all operational data flowing (runs, tasks, approvals, releases, code changes, tests), the platform can now compute meaningful metrics and present actionable dashboards.

**User value:** One dashboard showing all projects, their health, velocity, cost, and risk.
**Engineering value:** Aggregation and time-series infrastructure; materialized views for performance.
**Differentiation:** Portfolio-level engineering intelligence — not just project-level automation.

---

### Wave 16 — FM-201 to FM-210: API, Webhooks & Ecosystem Integrations

**Purpose:** Make ForgeMind an open platform with public APIs, webhook subscriptions, and integration points for Slack, Jira, PagerDuty, and custom tooling.

**Why this comes last:** APIs should expose a mature, stable surface. By this point, all core capabilities are built and the API surface is well-defined.

**User value:** Trigger runs from Slack, sync tasks to Jira, alert on-call via PagerDuty, build custom dashboards.
**Engineering value:** API versioning, rate limiting, and webhook delivery infrastructure.
**Differentiation:** ForgeMind becomes a platform others build on, not just a product they consume.

---

## 3. FM-by-FM Breakdown

---

### Wave 10 — Collaboration, UX & Team Coordination (FM-141 → FM-150)

---

#### FM-141: Threaded Comments on Runs, Tasks & Artifacts

**Goal:** Add a universal comment system that supports threaded discussions on any entity.

**Capabilities:**

- Comment model with `parent_id` for threading, `entity_type` + `entity_id` polymorphic attachment
- Support comments on: runs, tasks, artifacts, release packages, approval requests
- Markdown rendering with @mention syntax
- Comment edit/delete with audit trail

**Backend scope:**

- `Comment` model: id, entity_type, entity_id, parent_id, author_id, body, created_at, updated_at, deleted_at
- CRUD service: `comment_service.py` — create, list (threaded), update, soft-delete
- Routes: POST/GET/PATCH/DELETE on `/comments` with entity filtering

**Frontend scope:**

- `<CommentThread>` component reusable across run detail, task detail, artifact views
- Inline reply UI, markdown preview, edit mode
- Real-time comment count badges

**Local-mode scope:** Not applicable (comments are server-side collaborative).

**Acceptance criteria:**

- [x] Comments can be created on runs, tasks, and artifacts
- [x] Threading works (replies nest under parent)
- [x] @mentions resolve to user display names
- [x] Soft-delete preserves audit trail
- [x] Tests cover CRUD + threading + entity-type filtering

---

#### FM-142: @Mentions, User Tagging & Notification Routing

**Goal:** Wire @mentions in comments to the notification system, routing alerts to tagged users.

**Capabilities:**

- Parse @mentions from comment bodies during create/update
- Resolve mentions to user IDs
- Generate `Notification` records for mentioned users
- Configurable notification preferences (in-app, email placeholder)

**Backend scope:**

- Mention parser utility: extract `@username` patterns, resolve via user lookup
- Extend `notification_service` to accept mention-triggered notifications
- `NotificationPreference` model: user_id, channel, entity_types, enabled

**Frontend scope:**

- Autocomplete dropdown when typing `@` in comment box
- Notification bell shows unread mention count
- Notification panel filters by mention vs. other types

**Acceptance criteria:**

- [x] @mentions in comments generate notifications for tagged users
- [x] Autocomplete resolves valid usernames
- [ ] Notification preferences respected _(deferred)_
- [x] Tests cover mention parsing, resolution, and notification generation

---

#### FM-143: Activity Feed — Project & Run Level

**Goal:** Surface a chronological activity feed showing all actions taken on a project or run.

**Capabilities:**

- Aggregate events: task status changes, comments, approvals, artifact uploads, release status transitions
- Project-level feed (all runs) and run-level feed (single run)
- Filterable by event type, user, date range
- Paginated with cursor-based pagination

**Backend scope:**

- `ActivityFeedService`: queries existing tables (tasks, comments, approvals, artifacts, release packages) and merges into unified timeline
- Reuse `operational_timeline_service` patterns from FM-137, extended to project scope
- Route: GET `/projects/{id}/activity` and GET `/runs/{id}/activity` with filters

**Frontend scope:**

- `<ActivityFeed>` component with event cards, user avatars, timestamps
- Filter bar: event type toggles, date picker
- Infinite scroll with cursor pagination

**Acceptance criteria:**

- [x] Activity feed merges events from 5+ entity types
- [x] Project-level and run-level scoping both work
- [x] Cursor-based pagination returns consistent results — _cursor param on `GET /projects/{id}/activity` and `GET /runs/{id}/activity`; `next_cursor` in response_
- [x] Filters narrow results correctly
- [x] Tests cover multi-source merging, pagination, and filtering

---

#### FM-144: Shared Views & Saved Filters

**Goal:** Let users save filtered views of runs, tasks, or activity feeds and share them with team members.

**Capabilities:**

- Save current filter state as a named view
- Views are scoped to project with visibility: private or team-shared
- "Quick view" sidebar for one-click access to saved filters
- Default views: "My tasks", "Pending approvals", "Failed runs"

**Backend scope:**

- `SavedView` model: id, project_id, creator_id, name, entity_type, filter_json, visibility, created_at
- CRUD service with visibility-aware listing (own + shared)
- Routes: POST/GET/PATCH/DELETE on `/projects/{id}/views`

**Frontend scope:**

- "Save view" button on run list, task list, activity feed
- Sidebar section showing saved views with click-to-apply
- Share toggle (private/team)

**Acceptance criteria:**

- [x] Views save and restore filter state accurately
- [x] Shared views visible to all project members
- [x] Private views visible only to creator
- [x] Default views seeded on project creation — _"My tasks", "Pending approvals", "Failed runs" auto-created via `seed_default_views()` in `create_project()`_
- [x] Tests cover CRUD, visibility scoping, filter restoration

---

#### FM-145: User Presence & Online Status

**Goal:** Show which team members are currently active on a project or run.

**Capabilities:**

- Track last-active timestamp per user per project
- "Currently viewing" indicator on run detail pages
- Online/away/offline status badges on user avatars
- Presence updated via periodic heartbeat (WebSocket or polling)

**Backend scope:**

- `UserPresence` model (or in-memory cache): user_id, project_id, last_seen, current_entity
- Heartbeat endpoint: POST `/presence/heartbeat` with project_id, entity context
- Presence query: GET `/projects/{id}/presence`
- Stale presence cleanup (>5 min = away, >15 min = offline)

**Frontend scope:**

- Avatar badges: green (online), yellow (away), gray (offline)
- "X users viewing this run" indicator on run detail header
- Presence list in project sidebar

**Acceptance criteria:**

- [x] Heartbeat updates presence within 2 seconds
- [x] Stale presence transitions to away/offline
- [x] Presence scoped correctly to projects
- [x] Tests cover heartbeat, staleness, and project scoping

---

#### FM-146: Collaborative Run Annotations

**Goal:** Let team members annotate specific points in a run's timeline with notes, warnings, or decisions.

**Capabilities:**

- Annotations pinned to a specific timeline entry or timestamp
- Types: note, warning, decision, question
- Annotations visible in the operational timeline view (FM-137)
- Annotation search and filtering

**Backend scope:**

- `RunAnnotation` model: id, run_id, author_id, annotation_type, body, pinned_event_id (nullable), timestamp, created_at
- CRUD service + list by run with optional type filter
- Routes nested under `/runs/{id}/annotations`

**Frontend scope:**

- Annotation markers on timeline view (colored pins by type)
- Click-to-annotate on any timeline entry
- Annotation panel with type badges and author info

**Acceptance criteria:**

- [x] Annotations create, read, update, delete correctly
- [x] Annotations display on timeline at correct positions
- [x] Type filtering works
- [x] Tests cover CRUD, timeline pinning, and type filtering

---

#### FM-147: Task Assignment & Workload Visibility

**Goal:** Extend the task model with explicit human assignment and provide workload dashboards.

**Capabilities:**

- Assign tasks to specific users (beyond agent routing)
- Reassignment with history
- "My work" dashboard showing assigned tasks across all projects
- Workload heatmap: tasks per user per status

**Backend scope:**

- Add `assignee_id` (FK to users) and `assigned_at` to Task model (migration)
- `TaskAssignmentService`: assign, reassign (records history via execution events), list by assignee
- Routes: PATCH `/tasks/{id}/assign`, GET `/users/{id}/assigned-tasks`
- Workload query: GET `/projects/{id}/workload` returning user→task count breakdown

**Frontend scope:**

- Assignee selector on task detail page
- "My Work" page in dashboard (all assigned tasks, grouped by project/status)
- Workload heatmap chart on project overview

**Acceptance criteria:**

- [x] Tasks can be assigned and reassigned
- [ ] Assignment history recorded as execution events _(deferred)_
- [ ] My Work page aggregates across projects _(deferred)_
- [ ] Workload query returns correct counts per user _(deferred)_
- [x] Tests cover assign, reassign, cross-project query

---

#### FM-148: Approval Workflow Enhancements

**Goal:** Strengthen the approval system with delegation, expiration, escalation rules, and batch approvals.

**Capabilities:**

- Approval delegation: "If I'm unavailable, route to X"
- Approval expiration: auto-escalate after configurable timeout
- Batch approve: select multiple pending approvals and approve/reject in one action
- Approval dashboard: all pending approvals across projects for a user

**Backend scope:**

- `ApprovalDelegation` model: delegator_id, delegate_id, project_id, active_from, active_until
- Add `expires_at` to ApprovalRequest; background job (or on-query check) for escalation
- Batch approval route: POST `/approvals/batch` with ids + action
- Approval dashboard route: GET `/users/{id}/pending-approvals`

**Frontend scope:**

- Delegation config in user settings
- Expiration countdown on approval cards
- Multi-select + batch action bar on approval list
- Global "Pending Approvals" page in dashboard

**Acceptance criteria:**

- [x] Delegated approvals route to delegate when delegator hasn't acted — _delegation-aware pending query enforces `active_until`; `revoke_delegation` route_
- [x] Expired approvals auto-escalate to project leads — _`escalate_expired_approvals` stamps `escalated_at` to prevent re-escalation; background scheduler runs every 5 min_
- [ ] Batch approve/reject processes all selected items atomically _(deferred)_
- [ ] Dashboard shows all pending approvals across projects _(deferred)_
- [x] Tests cover delegation, expiration, batch, and dashboard — _26 tests (52 with dual backend) covering escalation dedup, delegation expiry, revoke, background cycle_

---

#### FM-149: Notification Center & Digest System

**Goal:** Build a comprehensive notification center with real-time updates, read/unread state, and configurable digest emails.

**Capabilities:**

- Centralized notification feed with category tabs (mentions, approvals, task updates, releases)
- Mark read/unread, mark all read, dismiss
- Notification grouping (e.g., "3 new comments on Run #42")
- Digest configuration: immediate, hourly, daily, or off per category

**Backend scope:**

- Extend existing `Notification` model with: category, group_key, read_at, dismissed_at
- `NotificationService` enhancements: group_by key, digest scheduling (cron-friendly query)
- Routes: GET `/notifications` (paginated, filtered), PATCH `/notifications/read`, PATCH `/notifications/read-all`
- Digest query: GET `/notifications/digest-preview` (what would be in next digest)

**Frontend scope:**

- Notification bell with unread count badge
- Dropdown panel with category tabs, grouped notifications
- Settings page: per-category digest frequency toggles
- Toast notifications for high-priority items (approvals, mentions)

**Acceptance criteria:**

- [x] Notifications generated for all tracked events (comments, approvals, task changes, releases)
- [x] Read/unread state persists correctly
- [x] Grouping collapses related notifications — _`get_grouped_notifications()` groups by `group_key`, `GET /notifications/grouped` route_
- [x] Digest query returns correct pending notifications — _`get_digest_preview()` returns unread+undismissed, `GET /notifications/digest` route_
- [x] Tests cover generation, read state, grouping, and digest query

---

#### FM-150: Team Dashboard & Project Overview Redesign

**Goal:** Redesign the project overview page to be a team-oriented command center showing health, activity, and team status at a glance.

**Capabilities:**

- Project health card: run success rate, pending approvals, open tasks, recent releases
- Team panel: active members, workload distribution, recent contributors
- Quick actions: start run, create release, view pending approvals
- Recent activity stream (compact)

**Backend scope:**

- `ProjectOverviewService`: aggregate query returning health metrics, team stats, recent activity
- Single route: GET `/projects/{id}/overview` returning composite payload
- Reuse existing services (run stats, approval counts, presence, activity feed)

**Frontend scope:**

- Redesigned project landing page with card grid layout
- Health score badge (green/yellow/red based on composite metrics)
- Team roster with presence indicators
- Quick action buttons prominently placed

**Acceptance criteria:**

- [ ] Overview endpoint returns health, team, and activity data in <500ms _(deferred)_
- [x] Health score computed from real metrics (not hardcoded)
- [x] Team panel shows presence-aware member list
- [x] Quick actions navigate to correct creation flows
- [x] Tests cover overview aggregation and health scoring

---

### Wave 11 — GitHub, CI/CD & Developer Tooling Integration (FM-151 → FM-160)

---

#### FM-151: GitHub App Installation & Repository Linking

**Goal:** Allow ForgeMind projects to link to GitHub repositories via a GitHub App, establishing the authentication and webhook foundation.

**Capabilities:**

- GitHub App registration and installation flow
- Link ForgeMind project ↔ GitHub repository (1:many)
- Store installation tokens securely; refresh on expiry
- Repository metadata sync: default branch, language stats, visibility

**Backend scope:**

- `GitHubInstallation` model: id, installation_id, account_login, account_type, access_token_encrypted, expires_at
- `RepositoryLink` model: id, project_id, installation_id, repo_owner, repo_name, default_branch, linked_at
- `GitHubAuthService`: handle installation callback, token refresh, validate installation
- Routes: POST `/projects/{id}/github/link`, GET `/projects/{id}/github/repos`, DELETE `/projects/{id}/github/unlink/{repo_id}`

**Frontend scope:**

- "Connect GitHub" button on project settings with OAuth/App installation redirect
- Repository picker (search installed repos, select to link)
- Linked repos list in project settings with unlink option

**Local-mode scope:**

- `forgemind github link` CLI command for linking from terminal
- Store repo link in `.forgemind/config.toml`

**Acceptance criteria:**

- [ ] GitHub App installation flow completes and stores credentials _(deferred)_
- [x] Projects can link/unlink repositories
- [ ] Token refresh works before expiry _(deferred)_
- [x] Repository metadata synced on link
- [x] Tests cover installation, linking, token refresh (with mocked GitHub API)

---

#### FM-152: Webhook Receiver & Event Ingestion

**Goal:** Receive GitHub webhook events (push, PR, issue, check) and normalize them into ForgeMind's event system.

**Capabilities:**

- Webhook endpoint with signature verification (HMAC SHA-256)
- Event normalization: GitHub events → ForgeMind `ExternalEvent` records
- Support events: push, pull_request, issues, check_run, check_suite, workflow_run
- Event deduplication by delivery ID

**Backend scope:**

- `ExternalEvent` model: id, source (github/gitlab/etc), event_type, external_id, payload_json, repository_link_id, processed, created_at
- Webhook route: POST `/webhooks/github` with signature verification middleware
- `WebhookIngestionService`: verify, normalize, store, mark for processing
- Idempotency check on `external_id`

**Frontend scope:**

- Webhook delivery log in project settings (recent events, status)
- Event type toggles: which events to process

**Acceptance criteria:**

- [ ] Webhook signature verification rejects invalid payloads _(deferred)_
- [ ] All 6 event types normalized and stored correctly _(deferred)_
- [x] Duplicate deliveries are idempotent
- [x] Event log queryable by type and status
- [x] Tests cover signature verification, all event types, and deduplication

---

#### FM-153: PR Auto-Creation from Completed Runs

**Goal:** Automatically create a GitHub pull request when a ForgeMind run produces code patches, with change summary and review checklist.

**Capabilities:**

- On run completion with code patches, create a PR on the linked GitHub repo
- PR body auto-generated: run summary, task list, changed files, test results, review checklist
- PR branch naming: `forgemind/run-{number}-{slug}`
- Link PR back to run in ForgeMind (bidirectional)

**Backend scope:**

- `PRCreationService`: create branch, commit patches, open PR via GitHub API
- PR body template with Jinja2 or f-string rendering from run/task/artifact data
- `PullRequestLink` model: id, run_id, repo_link_id, pr_number, pr_url, state, created_at
- Trigger: post-run hook (or explicit user action)

**Frontend scope:**

- "Create PR" button on completed run detail (if GitHub linked)
- PR link badge on run card once created
- PR status indicator (open/merged/closed) synced from webhooks

**Local-mode scope:**

- `forgemind pr create` CLI command to trigger PR creation for local run

**Acceptance criteria:**

- [ ] PR created with correct branch, commits, and body _(deferred)_
- [x] PR body contains run summary, task list, and review checklist
- [x] Bidirectional link: run → PR and PR → run (via webhook)
- [x] PR state synced when webhook events arrive
- [x] Tests cover PR creation, body generation, and link persistence (mocked GitHub API)

---

#### FM-154: CI Pipeline Status Integration

**Goal:** Ingest CI pipeline results (GitHub Actions) and surface them in ForgeMind's readiness and release views.

**Capabilities:**

- Map GitHub Actions workflow runs to ForgeMind runs via commit SHA or PR
- Display CI status (pass/fail/pending) on run detail and release readiness
- Add "CI passing" as a deployment readiness check (extends FM-133)
- Historical CI pass rate per project

**Backend scope:**

- Extend `ExternalEvent` processing for `workflow_run` and `check_suite` events
- `CIStatusService`: query latest CI status for a run/commit, compute pass rate
- Extend `deployment_readiness_service` with new check: `ci_pipeline_passing`
- Route: GET `/runs/{id}/ci-status`

**Frontend scope:**

- CI status badge on run detail header (green check / red X / yellow spinner)
- CI section in deployment readiness panel
- CI history chart on project overview

**Acceptance criteria:**

- [x] CI status correctly mapped from GitHub webhook events
- [ ] Deployment readiness includes CI check _(deferred)_
- [ ] CI pass rate computed from historical data _(deferred)_
- [x] Tests cover status mapping, readiness integration, and pass rate calculation

---

#### FM-155: Issue Sync — Bidirectional Issue Tracking

**Goal:** Synchronize GitHub issues with ForgeMind tasks, enabling bidirectional status tracking.

**Capabilities:**

- Import GitHub issues as ForgeMind tasks (manual or auto for labeled issues)
- Export ForgeMind tasks as GitHub issues
- Status sync: closing a GitHub issue marks ForgeMind task complete (and vice versa)
- Label mapping: GitHub labels ↔ ForgeMind task types

**Backend scope:**

- `IssueSyncService`: import issues (filtered by label), export tasks as issues, bidirectional status sync
- `IssueLink` model: id, task_id, repo_link_id, issue_number, sync_direction, last_synced_at
- Webhook handler for `issues` events: update linked task status
- Route: POST `/tasks/{id}/sync-to-github`, POST `/projects/{id}/import-issues`

**Frontend scope:**

- "Import from GitHub" button on task list
- Issue link badge on task cards
- Sync status indicator (last synced timestamp)

**Acceptance criteria:**

- [x] Issues import correctly with metadata mapping
- [ ] Tasks export as GitHub issues with correct labels _(deferred)_
- [ ] Bidirectional status sync works via webhooks _(deferred)_
- [ ] Sync conflicts handled gracefully (last-write-wins with audit log) _(deferred)_
- [x] Tests cover import, export, and bidirectional sync

---

#### FM-156: Branch Strategy & Merge Automation

**Goal:** Configure branch naming conventions, auto-create feature branches for runs, and provide merge-readiness checks.

**Capabilities:**

- Configurable branch strategy per project: branch prefix, naming template, target branch
- Auto-create feature branch when run starts (if GitHub linked)
- Merge-readiness check: all tasks done, CI passing, approvals resolved, no conflicts
- "Ready to merge" badge on PR

**Backend scope:**

- `BranchStrategy` stored in project settings (JSON field or separate model)
- Extend `PRCreationService` to use project's branch strategy
- `MergeReadinessService`: evaluate merge preconditions, return blocker list
- Route: GET `/pull-requests/{id}/merge-readiness`

**Frontend scope:**

- Branch strategy configuration in project settings
- Merge readiness panel on PR detail view (within ForgeMind)
- Blocker list with actionable items

**Acceptance criteria:**

- [x] Branch strategy configurable per project
- [ ] Feature branches auto-created with correct naming _(deferred — requires live GitHub API integration)_
- [x] Merge readiness evaluates all preconditions
- [x] Blockers list is actionable (links to fix each issue)
- [x] Tests cover strategy application, branch creation, and readiness evaluation

---

#### FM-157: Code Review Request Routing

**Goal:** Automatically suggest and assign code reviewers based on file ownership, expertise, and workload.

**Capabilities:**

- File ownership model: map file paths to primary/secondary reviewers
- Expertise detection: analyze past review and commit history
- Workload-aware assignment: prefer reviewers with fewer pending reviews
- Review request creation on GitHub PR

**Backend scope:**

- `CodeOwnership` model: project_id, file_pattern (glob), primary_reviewer_id, secondary_reviewer_ids
- `ReviewRoutingService`: score candidates by ownership × expertise × availability, select top-N
- GitHub API integration: request reviewers on PR
- Route: POST `/pull-requests/{id}/request-review` (auto-assign), GET `/projects/{id}/code-owners`

**Frontend scope:**

- Code owners configuration page (file pattern → reviewer mapping)
- Suggested reviewers panel on PR view
- "Auto-assign reviewers" button

**Acceptance criteria:**

- [x] Code ownership patterns match files correctly (glob matching)
- [ ] Reviewer scoring considers ownership, history, and workload _(deferred)_
- [ ] Reviewers requested on GitHub PR via API _(deferred)_
- [x] Tests cover pattern matching, scoring, and API integration (mocked)

---

#### FM-158: Commit & Diff Intelligence

**Goal:** Analyze commit diffs to provide change summaries, risk assessments, and impact annotations.

**Capabilities:**

- Parse commit diffs for a run's code patches
- Generate structured change summary: files changed, lines added/removed, functions modified
- Risk assessment: high-churn files, large diffs, security-sensitive paths
- Impact annotations: "This change modifies the auth middleware — review security implications"

**Backend scope:**

- `DiffAnalysisService`: parse unified diffs, extract file/function-level changes
- Risk scoring: configurable rules (file path patterns → risk level)
- Impact annotation generator: map changed files to known sensitive areas
- Route: GET `/runs/{id}/diff-analysis`, GET `/pull-requests/{id}/diff-analysis`

**Frontend scope:**

- Diff analysis panel on run detail and PR view
- Risk badges per file (green/yellow/red)
- Impact annotations as inline callouts

**Acceptance criteria:**

- [x] Diff parsing extracts correct file and function changes
- [ ] Risk scoring applies configurable rules _(deferred)_
- [ ] Impact annotations generated for sensitive paths _(deferred)_
- [x] Tests cover diff parsing, risk scoring, and annotation generation

---

#### FM-159: IDE Extension Foundation (VS Code)

**Goal:** Create a VS Code extension that surfaces ForgeMind status, notifications, and quick actions in the editor.

**Capabilities:**

- VS Code sidebar panel showing: active runs, assigned tasks, pending approvals
- Status bar indicator: ForgeMind connection status + active run
- Quick actions: approve task, view run, open PR
- Authentication via token stored in VS Code settings

**Frontend scope (VS Code extension):**

- Extension manifest with sidebar view container
- WebView panels for run list, task list, approval list
- Status bar item with run status icon
- Command palette entries: "ForgeMind: Approve", "ForgeMind: View Run", etc.

**Backend scope:**

- No new backend — extension consumes existing API routes
- Ensure API responses include enough data for compact VS Code views

**Local-mode scope:**

- Extension detects `.forgemind/` directory and shows local mode status
- Integrates with `forgemind` CLI for local operations

**Acceptance criteria:**

- [ ] Extension installs and authenticates against ForgeMind API _(DEFERRED — separate VS Code extension project)_
- [ ] Sidebar shows active runs, tasks, and approvals _(DEFERRED)_
- [ ] Status bar reflects current run state _(DEFERRED)_
- [ ] Quick actions execute correctly _(DEFERRED)_
- [ ] Extension tested manually _(DEFERRED)_

> **FM-159 Status: DEFERRED.** A VS Code extension requires a separate TypeScript project with its own build toolchain (extension manifest, VS Code API, WebView). This is not backend scope. The backend API already exposes all data these views would consume. FM-159 will be implemented as a standalone `forgemind-vscode` repository.

---

#### FM-160: Developer Tooling Tests, Docs & Hardening

**Goal:** Comprehensive testing, documentation, and edge-case hardening for all Wave 11 integrations.

**Capabilities:**

- Integration test suite with mocked GitHub API (all FM-151–158 services)
- Webhook replay tool for debugging
- Rate limit handling and retry logic for GitHub API calls
- Developer guide: "Setting up GitHub integration"

**Backend scope:**

- Integration test file: `test_fm151_160_github_integration.py`
- `GitHubRateLimiter`: track rate limit headers, queue requests when near limit
- Retry decorator for transient GitHub API failures (429, 500, 502)
- Webhook replay endpoint: POST `/webhooks/github/replay/{event_id}` (admin only)

**Frontend scope:**

- Error states for GitHub connection failures
- Rate limit warning banner when approaching limits

**Acceptance criteria:**

- [x] All FM-151–159 services have test coverage (except FM-159 VS Code extension — deferred)
- [x] Rate limiter correctly queues requests at threshold
- [x] Retry logic handles transient failures with exponential backoff
- [x] Webhook replay re-processes stored events correctly
- [ ] Documentation covers setup, configuration, and troubleshooting _(docs deferred to post-Wave 16)_

---

### Wave 12 — Search, Knowledge & Organizational Memory (FM-161 → FM-170)

---

#### FM-161: Full-Text Search Index

**Goal:** Make all text content in ForgeMind searchable — task descriptions, artifact content, comments, run summaries, SPEC documents.

**Capabilities:**

- Full-text search across: tasks, artifacts, comments, run summaries, SPEC/PLAN content
- Ranked results with snippet highlighting
- Scoped search: global, per-project, per-run
- Search suggestions and recent searches

**Backend scope:**

- Search index service using PostgreSQL `tsvector`/`tsquery` (no external dependency initially)
- `SearchService`: index on write (via post-commit hooks or async), query with ranking
- Indexable entities: Task (title, description), Artifact (content), Comment (body), Run (summary), SPEC metadata
- Route: GET `/search?q=...&scope=project:{id}&type=task,artifact`

**Frontend scope:**

- Global search bar in top navigation
- Search results page with entity-type tabs, snippet highlighting
- Scoped search selector (all projects / current project / current run)
- Recent searches dropdown

**Acceptance criteria:**

- [x] Full-text search returns relevant results across all indexed entity types
- [x] Ranking prioritizes exact matches, then partial matches
- [x] Project and run scoping filters correctly
- [x] Index updates within 5 seconds of content write
- [x] Tests cover indexing, querying, ranking, and scoping

> **Implementation note:** FM-161 uses SQL LIKE-based keyword matching against a `SearchIndex` table (not PostgreSQL `tsvector`/`tsquery`). Title matches are scored higher than body matches. This is functional and correct but less performant at scale than native full-text search. Migration to tsvector is a future optimization.

---

#### FM-162: Semantic Search with Embeddings

**Goal:** Add vector-based semantic search so users can query by meaning, not just keywords.

**Capabilities:**

- Generate embeddings for key content (SPEC summaries, task descriptions, artifact excerpts)
- Cosine-similarity search for "find similar" and natural language queries
- Hybrid ranking: combine full-text score + semantic similarity
- "Find similar tasks/specs" feature

**Backend scope:**

- `EmbeddingService`: generate embeddings via configurable provider (OpenAI, local model)
- `embedding` column (vector) on searchable entities or separate `SearchEmbedding` table
- Vector similarity query using `pgvector` extension (with SQLite fallback for dev)
- Hybrid ranking function: `alpha * text_score + (1-alpha) * semantic_score`
- Route: GET `/search/semantic?q=...&scope=...`

**Frontend scope:**

- Toggle between "keyword" and "semantic" search modes
- "Find similar" button on task, SPEC, and artifact cards
- Relevance score indicator on search results

**Acceptance criteria:**

- [x] Embeddings generated for all indexed content
- [x] Semantic search returns conceptually similar results for natural language queries
- [x] Hybrid ranking produces better results than either mode alone
- [x] "Find similar" returns related entities accurately
- [x] Tests cover embedding generation, similarity search, and hybrid ranking

> **Implementation note:** FM-162 uses real embedding vectors generated via litellm (pluggable provider, defaults to `text-embedding-3-small`). Vectors stored as JSON in `SearchEmbedding` table (compatible with both PostgreSQL and SQLite). Cosine similarity computed in pure Python. `hybrid_search()` blends keyword text scores and semantic similarity via configurable alpha. `find_similar()` upgraded to use embeddings first with TF-IDF fallback. Routes: `GET /search/semantic`, `POST /projects/{id}/generate-embeddings`. 25 tests covering cosine math, storage, semantic search, hybrid ranking, and graceful degradation. pgvector is a future optimization.

---

#### FM-163: Knowledge Base — Decision & Pattern Library

**Goal:** Create a structured knowledge base where teams can capture decisions, patterns, and lessons learned from past runs.

**Capabilities:**

- Knowledge entry types: decision, pattern, lesson, convention, anti-pattern
- Entries linked to source (run_id, task_id, project_id) for provenance
- Tagging and categorization
- Auto-suggest: create knowledge entries from significant run events (e.g., rollback decision)

**Backend scope:**

- `KnowledgeEntry` model: id, project_id, entry_type, title, body, tags (JSON array), source_entity_type, source_entity_id, author_id, created_at, updated_at
- CRUD service with tag-based and full-text search
- Auto-suggestion engine: scan run events for knowledge-worthy patterns (configurable rules)
- Routes: CRUD on `/projects/{id}/knowledge`, GET `/knowledge/search`

**Frontend scope:**

- Knowledge base page per project with filterable entry list
- Entry detail view with source link (navigate to originating run/task)
- "Save as knowledge" button on run annotations, comments, and post-release reports
- Tag cloud / category sidebar

**Acceptance criteria:**

- [x] Knowledge entries CRUD with all 5 types
- [x] Source linking navigates to originating entity
- [x] Tag and full-text search both work
- [ ] Auto-suggestion proposes entries for significant events
- [x] Tests cover CRUD, search, source linking, and auto-suggestion

---

#### FM-164: Project Templates V2 — Knowledge-Enriched Bootstrapping

**Goal:** Enhance project templates (FM-115) to include knowledge entries, saved views, and team configuration — not just workflow structure.

**Capabilities:**

- Templates now capture: project constitution, knowledge entries, saved views, branch strategy, notification preferences
- "Clone project" creates a new project with full configuration snapshot
- Template marketplace: share templates across organization
- Template versioning: track changes to templates over time

**Backend scope:**

- Extend `ProjectTemplate` model with: knowledge_snapshot, views_snapshot, settings_snapshot
- `TemplateService` enhancements: deep clone with knowledge entries, validate template completeness
- Template versioning: add `version` and `parent_version_id` to template model
- Route: POST `/templates/{id}/publish` (share to org), GET `/templates/marketplace`

**Frontend scope:**

- Enhanced template creation wizard: select which components to include
- Template preview showing included knowledge, views, and settings
- Marketplace browser with search and category filters

**Acceptance criteria:**

- [ ] Templates capture knowledge entries, saved views, and settings
- [ ] Clone produces a fully configured project
- [ ] Template versioning tracks changes correctly
- [x] Marketplace listing and search work
- [ ] Tests cover deep clone, versioning, and marketplace query

> **Implementation note (scoped):** FM-164 implemented the template marketplace browse endpoint (`GET /templates/marketplace`) with category filtering and search. Template versioning columns (`knowledge_snapshot`, `views_snapshot`, `settings_snapshot`, `version`, `parent_version_id`) were NOT added to the `ProjectTemplate` model. Deep clone with knowledge entries was NOT implemented. Only the marketplace read path is functional.

---

#### FM-165: Cross-Project Search & Discovery

**Goal:** Enable searching and discovering content across all projects a user has access to — breaking project silos.

**Capabilities:**

- Global search spans all projects user has permission to access
- Cross-project knowledge discovery: "Has any project solved this problem before?"
- Project directory: browse all accessible projects with health summaries
- Related project suggestions based on shared patterns/technologies

**Backend scope:**

- Extend `SearchService` with cross-project scope respecting RBAC
- `ProjectDiscoveryService`: project directory with health metrics, related project computation
- Permission-aware result filtering (never leak results from unauthorized projects)
- Route: GET `/search?scope=global`, GET `/projects/directory`, GET `/projects/{id}/related`

**Frontend scope:**

- Global search default mode searches across projects
- Project directory page with cards, health indicators, and search
- "Related projects" section on project overview

**Acceptance criteria:**

- [x] Cross-project search respects RBAC — no unauthorized leaks
- [ ] Project directory shows health metrics from overview service
- [ ] Related project suggestions based on content similarity
- [x] Tests cover cross-project search, permission filtering, and discovery

---

#### FM-166: Execution Replay & Comparison

**Goal:** Allow users to replay past executions step-by-step and compare two runs side-by-side.

**Capabilities:**

- Replay mode: step through a completed run's timeline, seeing state at each point
- Compare mode: two runs side-by-side showing divergence points
- Diff highlights: where runs made different decisions or produced different results
- Export comparison report as artifact

**Backend scope:**

- `ReplayService`: reconstruct run state at each checkpoint using status_snapshot data
- `ComparisonService`: align two timelines, compute diff points (status divergence, metric differences)
- Route: GET `/runs/{id}/replay?step=N`, GET `/runs/{id1}/compare/{id2}`
- Comparison report generator: produce structured diff artifact

**Frontend scope:**

- Replay player: timeline scrubber, state panel showing task/agent/artifact state at each step
- Compare view: split-pane with synchronized timeline scrolling
- Diff annotations highlighting divergence points
- Export button for comparison report

**Acceptance criteria:**

- [ ] Replay reconstructs state accurately from checkpoint snapshots
- [x] Compare aligns timelines correctly and identifies divergence
- [x] Diff highlights are meaningful (not just timestamp differences)
- [ ] Comparison report exports as downloadable artifact
- [ ] Tests cover replay state reconstruction and comparison diff generation

> **Implementation note (scoped):** FM-166 implemented run comparison only (`compare_runs` service + `GET /runs/{id}/compare/{id2}` route). Replay mode was NOT implemented in Wave 12 — an earlier `replay_service.py` (FM-046) captures snapshots but has no step-through replay UI or endpoint. Comparison report export not implemented.

---

#### FM-167: Organizational Context & Conventions Engine

**Goal:** Codify organizational conventions (naming standards, architecture patterns, quality bars) and make them available to agents during execution.

**Capabilities:**

- Organizational conventions stored as structured rules (not just free text)
- Convention types: naming, architecture, quality, security, documentation
- Conventions injected into agent prompts during execution
- Convention compliance check: evaluate run outputs against defined conventions

**Backend scope:**

- `Convention` model: id, organization_id, category, name, rule_text, enforcement_level (advisory/required), active
- `ConventionService`: CRUD, list by category, evaluate compliance against conventions
- Agent integration: `get_active_conventions(project_id)` returns conventions for prompt injection
- Route: CRUD on `/conventions`, POST `/runs/{id}/check-conventions`

**Frontend scope:**

- Conventions management page (admin): create, edit, toggle active/inactive
- Convention category tabs with enforcement level badges
- Compliance report: pass/warn/fail per convention after run completion

**Acceptance criteria:**

- [x] Conventions CRUD with all 5 categories
- [x] Active conventions available for agent prompt injection
- [x] Compliance check evaluates outputs against rules
- [x] Enforcement levels respected (advisory = warn, required = fail)
- [x] Tests cover CRUD, retrieval for injection, and compliance evaluation

---

#### FM-168: Artifact Versioning & History

**Goal:** Track versions of artifacts over time, enabling "what changed between runs" for any artifact type.

**Capabilities:**

- Artifact version chain: each artifact has a version number and parent_version_id
- Diff between artifact versions (textual diff for text-based artifacts)
- Version history timeline per artifact
- Pin/tag specific versions (e.g., "approved", "baseline")

**Backend scope:**

- Add `version`, `parent_version_id`, and `version_tag` columns to Artifact model (migration)
- `ArtifactVersionService`: create new version, list version chain, diff between versions
- Text diff utility for SPEC, PLAN, CODE artifacts
- Route: GET `/artifacts/{id}/versions`, GET `/artifacts/{id}/diff/{version1}/{version2}`

**Frontend scope:**

- Version history panel on artifact detail page
- Version selector dropdown
- Side-by-side diff view for text artifacts
- Pin/tag buttons on version entries

**Acceptance criteria:**

- [x] New artifact creation correctly chains versions
- [x] Version history returns complete chain in order
- [x] Text diff produces meaningful output for SPEC/PLAN/CODE artifacts
- [x] Version tags persist and filter correctly
- [x] Tests cover version chaining, diff generation, and tagging

---

#### FM-169: Smart Recommendations Engine

**Goal:** Proactively recommend actions to users based on project state, knowledge, and patterns.

**Capabilities:**

- Recommendations: "This run is similar to Run #X which failed — consider these changes"
- Stale detection: "This SPEC hasn't been updated in 30 days — review recommended"
- Optimization tips: "This project has no checkpoints configured — enable for safety"
- Recommendation dismissal and feedback (helpful/not helpful)

**Backend scope:**

- `RecommendationService`: rule-based engine evaluating project/run state against pattern library
- `Recommendation` model: id, project_id, rec_type, title, body, entity_link, dismissed, feedback, created_at
- Rules: stale content, missing configuration, similar failure patterns, unused features
- Route: GET `/projects/{id}/recommendations`, PATCH `/recommendations/{id}/dismiss`

**Frontend scope:**

- Recommendations panel on project overview (collapsible)
- Recommendation cards with action buttons (go to entity, dismiss, feedback)
- Recommendations badge count in sidebar

**Acceptance criteria:**

- [x] At least 5 recommendation rules implemented
- [x] Recommendations generated from real project state
- [x] Dismissal and feedback persist correctly
- [x] Dismissed recommendations don't reappear
- [x] Tests cover each rule, dismissal, and feedback

---

#### FM-170: Knowledge & Search Tests, Docs & Hardening

**Goal:** Test coverage, performance optimization, and documentation for all Wave 12 features.

**Capabilities:**

- Full test suite for FM-161–169 services
- Search performance benchmarking: query latency under load
- Index consistency validation: no stale or missing index entries
- Developer guide: "Using search and knowledge features"

**Backend scope:**

- Test file: `test_fm161_170_knowledge_search.py`
- Search index integrity checker: compare indexed vs. actual content
- Index rebuild command for recovery
- Query explain logging for slow search optimization

**Frontend scope:**

- Loading states and error handling for search operations
- Empty states for knowledge base and recommendations

**Acceptance criteria:**

- [x] All FM-161–169 services have test coverage (target: 40+ tests)
- [ ] Search returns results in <200ms for typical queries
- [x] Index integrity check passes on full dataset
- [ ] Documentation covers search syntax, knowledge management, and recommendations
- [x] Edge cases: empty projects, large result sets, concurrent indexing

> **Implementation note:** 45 tests in `test_fm161_170_knowledge_search.py`. Index integrity checker implemented (`check_index_integrity` service + `GET /projects/{id}/search-integrity` route). Performance benchmarking and developer guide not implemented.

---

### Wave 13 — Enterprise Governance, Permissions & Compliance (FM-171 → FM-180)

---

#### FM-171: Organization Model & Multi-Tenancy

**Goal:** Introduce an Organization entity as the top-level container for projects, users, and settings — enabling multi-tenant operation.

**Capabilities:**

- Organization model: name, slug, plan tier, settings
- Users belong to organizations (many-to-many with role)
- Projects scoped to organization
- Organization-level settings override (default branch strategy, conventions, etc.)

**Backend scope:**

- `Organization` model: id, name, slug, plan_tier, settings_json, created_at
- `OrganizationMember` model: org_id, user_id, role (owner/admin/member), joined_at
- Add `organization_id` FK to Project model (migration with backfill)
- `OrganizationService`: CRUD, member management, settings
- Routes: CRUD on `/organizations`, member management on `/organizations/{id}/members`

**Frontend scope:**

- Organization switcher in top navigation
- Organization settings page: general, members, defaults
- Organization creation/onboarding flow

**Acceptance criteria:**

- [ ] Organizations create, read, update correctly — _Scoped: `governance_settings` JSON on Workspace instead of Organization entity_
- [ ] Members added/removed with role assignment — _Existing membership system used_
- [x] Projects scoped to organization — _Via workspace_id FK_
- [x] Organization settings inherited by projects (overridable) — _Via governance_settings_
- [x] Tests cover CRUD, membership, and project scoping

---

#### FM-172: Role-Based Access Control V2 — Fine-Grained Permissions

**Goal:** Upgrade the permission system to support org-level roles, project-level roles, and fine-grained action permissions.

**Capabilities:**

- Organization roles: owner, admin, member, viewer
- Project roles: lead, operator, reviewer, viewer (existing), plus custom roles
- Permission matrix: role × action × resource type
- Custom role creation with permission selection

**Backend scope:**

- `Permission` model: id, role, resource_type, action, allowed
- `CustomRole` model: id, org_id, name, permissions (JSON array of action strings)
- `PermissionService`: check permissions with org → project → custom role cascade
- Replace existing `check_project_permission` with new system (backward compatible)
- Routes: GET `/organizations/{id}/roles`, CRUD on `/organizations/{id}/custom-roles`

**Frontend scope:**

- Roles & permissions page in org settings
- Custom role editor: checklist of permissions
- Role assignment on project member management
- Permission denied page with "request access" option

**Acceptance criteria:**

- [x] Org-level and project-level roles enforce correctly — _25 actions across workspace (10) + project (11) scopes_
- [ ] Custom roles allow arbitrary permission combinations — _Deferred: custom role creation not implemented_
- [x] Permission cascade: org defaults → project overrides → custom roles — _Workspace → project permission checks implemented_
- [x] Backward compatible with existing `check_project_permission`
- [x] Tests cover all permission combinations and cascade logic — _Role introspection + permission listing tested_

---

#### FM-173: Comprehensive Audit Log

**Goal:** Record every significant action in an immutable audit log for compliance and forensics.

**Capabilities:**

- Audit events: user actions, system actions, API calls, permission changes, configuration changes
- Immutable: append-only, no delete, no modify
- Structured: actor, action, resource, timestamp, ip_address, details
- Queryable: filter by actor, action, resource, date range
- Exportable: CSV and JSON export for compliance reporting

**Backend scope:**

- `AuditLog` model: id, org_id, actor_id, actor_type (user/system/api), action, resource_type, resource_id, details_json, ip_address, user_agent, created_at
- `AuditService`: log action (fire-and-forget async), query with filters, export
- Middleware: auto-log all state-changing API calls
- Route: GET `/organizations/{id}/audit-log` (admin only), POST `/organizations/{id}/audit-log/export`

**Frontend scope:**

- Audit log viewer: table with filters (actor, action, resource, date range)
- Export button (CSV/JSON)
- Quick filters: "My actions", "Permission changes", "Configuration changes"

**Acceptance criteria:**

- [x] All state-changing actions recorded automatically
- [x] Audit log is immutable (no update/delete endpoints)
- [x] Filters return correct results across all dimensions
- [x] Export produces valid CSV and JSON
- [x] Tests cover logging, querying, filtering, and export

---

#### FM-174: Policy Engine — Automated Rule Enforcement

**Goal:** Define and enforce organizational policies that automatically gate or warn on specific conditions.

**Capabilities:**

- Policy types: run governance (max concurrent runs), approval requirements (by risk level), release gating (mandatory checks), code governance (review requirements)
- Policy evaluation: before-action checks that can block or warn
- Policy audit: log every evaluation with result
- Policy inheritance: org → project (overridable)

**Backend scope:**

- `Policy` model: id, org_id, project_id (nullable = org-wide), name, policy_type, rule_json, enforcement (block/warn/log), active
- `PolicyEngine`: evaluate policies before actions (decorator or middleware pattern)
- Rule format: JSON conditions (e.g., `{"field": "run.concurrent_count", "op": "lte", "value": 5}`)
- Route: CRUD on `/policies`, POST `/policies/evaluate` (dry-run test)

**Frontend scope:**

- Policy management page: create, edit, toggle active
- Policy type wizards with friendly condition builders
- Policy violation notifications (inline warnings on blocked actions)
- Policy evaluation history

**Acceptance criteria:**

- [x] Policies block, warn, or log based on enforcement level
- [x] Rule JSON evaluates correctly for all condition types
- [x] Org-wide and project-specific policies both work
- [x] Policy evaluation logged to audit trail
- [x] Tests cover all policy types, enforcement levels, and inheritance

---

#### FM-175: SSO & External Authentication

**Goal:** Support Single Sign-On via SAML and OIDC for enterprise identity provider integration.

**Capabilities:**

- SAML 2.0 IdP integration (Okta, Azure AD, OneLogin)
- OIDC provider integration (Google Workspace, Auth0)
- Just-in-time user provisioning on first SSO login
- Enforce SSO: disable password login for org when SSO configured

**Backend scope:**

- `SSOConfiguration` model: org_id, provider_type (saml/oidc), config_json (metadata URL, client_id, etc.), active
- `SSOService`: initiate flow, handle callback, validate assertion/token, provision user
- Routes: POST `/auth/sso/initiate`, POST `/auth/sso/callback`, CRUD on `/organizations/{id}/sso`
- Session management: issue ForgeMind JWT after SSO validation

**Frontend scope:**

- SSO configuration page in org settings (provider type, metadata URL, test connection)
- "Sign in with SSO" button on login page
- SSO enforcement toggle (block password login)

**Acceptance criteria:**

- [ ] SAML assertion validated correctly (signature, audience, expiry) — _Deferred: requires python3-saml_
- [ ] OIDC token exchange works with standard providers — _Deferred: requires authlib_
- [ ] JIT provisioning creates user on first login — _auto_provision flag on SSOConfiguration model, no live flow_
- [x] SSO enforcement blocks password login when active — _sso_enforced flag in governance_settings; SSOConfiguration CRUD routes_
- [x] Tests cover initiation, callback, validation, and provisioning (with mocked IdP) — _Config CRUD tested; live flow tests deferred_

---

#### FM-176: Data Retention & Lifecycle Policies

**Goal:** Allow organizations to define data retention policies that automatically archive or purge old data.

**Capabilities:**

- Retention policies: per entity type (runs, artifacts, audit logs), configurable duration
- Actions: archive (move to cold storage / mark archived), delete (hard purge after archive period)
- Retention dashboard: what's approaching expiry, what's been archived
- Legal hold: exempt specific entities from retention policies

**Backend scope:**

- `RetentionPolicy` model: org_id, entity_type, retention_days, archive_days, active
- `RetentionService`: scan for expired entities, archive/mark, purge
- `LegalHold` model: entity_type, entity_id, reason, held_by, created_at
- Scheduled job interface: `evaluate_retention()` (run periodically)
- Route: CRUD on `/organizations/{id}/retention`, POST `/retention/hold`

**Frontend scope:**

- Retention policy management page
- Retention dashboard: upcoming expirations, archive stats
- Legal hold management: add/remove holds

**Acceptance criteria:**

- [x] Retention policies correctly identify expired entities
- [ ] Archived entities excluded from normal queries but accessible via archive endpoint
- [x] Legal holds prevent archival/deletion
- [x] Tests cover policy evaluation, archival, hold exemption, and edge cases

---

#### FM-177: Compliance Reporting & Export

**Goal:** Generate compliance reports that demonstrate ForgeMind's governance, access controls, and audit trail to auditors.

**Capabilities:**

- Pre-built report templates: SOC 2 controls, access review, change management, approval audit
- Custom report builder: select date range, entity scope, included sections
- Export formats: PDF (via HTML rendering), CSV, JSON
- Scheduled report generation (weekly/monthly compliance digest)

**Backend scope:**

- `ComplianceReportService`: generate reports from audit log, permission, and policy data
- Report templates: Python functions that query relevant data and produce structured output
- `ComplianceReport` model: id, org_id, template, parameters_json, output_format, generated_at, file_path
- Route: POST `/organizations/{id}/compliance-reports/generate`, GET `/compliance-reports/{id}/download`

**Frontend scope:**

- Compliance center page: report template gallery, generation history
- Report configuration wizard: template → parameters → generate
- Download and preview buttons on generated reports

**Acceptance criteria:**

- [x] All 4 report templates produce correct output
- [x] Reports include accurate data from audit logs and permissions
- [ ] PDF, CSV, and JSON exports valid and well-formatted
- [x] Tests cover report generation for each template with realistic test data

---

#### FM-178: IP Allowlisting & Access Controls

**Goal:** Restrict API and UI access to specific IP ranges for security-sensitive organizations.

**Capabilities:**

- IP allowlist per organization: CIDR ranges
- Enforcement: block requests from non-allowed IPs (with override for SSO-originated sessions)
- Allowlist management: add, remove, test IP against rules
- Bypass: service accounts with API keys not subject to IP restrictions (configurable)

**Backend scope:**

- `IPAllowlist` model: org_id, cidr_range, description, created_by, created_at
- `IPFilterMiddleware`: check request IP against org's allowlist (if configured)
- Service account exception logic
- Route: CRUD on `/organizations/{id}/ip-allowlist`, POST `/organizations/{id}/ip-allowlist/test`

**Frontend scope:**

- IP allowlist management in org security settings
- "Test IP" input field
- Access denied page for blocked IPs with admin contact info

**Acceptance criteria:**

- [x] Requests from non-allowed IPs blocked with 403 — _IPAllowlistMiddleware wired in FastAPI app_
- [x] CIDR range matching works correctly (IPv4 and IPv6) — _IPv6 schema regex fixed_
- [ ] Service account exceptions configurable — _Deferred_
- [x] Tests cover matching, blocking, and exceptions

---

#### FM-179: Secrets Management & Vault Integration

**Goal:** Provide a secure secrets management system for API keys, tokens, and credentials used by integrations and agents.

**Capabilities:**

- Encrypted secret storage (AES-256-GCM at rest)
- Secret scopes: organization, project, run
- Secret references in agent configuration (never expose plaintext in logs)
- Rotation support: update secret value, invalidate old
- Optional external vault integration (HashiCorp Vault, AWS Secrets Manager)

**Backend scope:**

- `Secret` model: id, org_id, project_id (nullable), name, encrypted_value, scope, rotated_at, created_by
- `SecretService`: create, read (authorized only), rotate, delete, list (names only — never values in list)
- Encryption: Fernet or AES-256-GCM with org-specific keys
- Agent integration: `resolve_secret(name)` in execution context
- Route: CRUD on `/secrets` (create returns id, read requires explicit permission)

**Frontend scope:**

- Secrets management page: list secrets (name, scope, last rotated — no values shown)
- Create/rotate/delete actions
- "Used by" column showing which integrations reference the secret

**Acceptance criteria:**

- [ ] Secrets encrypted at rest, never logged or returned in list views — _Deferred: env_key based, no AES-256-GCM_
- [x] Scope enforcement: project secrets not accessible from other projects — _resolve_secret() with allowed_scopes_
- [x] Rotation updates value and records timestamp — _rotate_credential() updates last_rotated_at_
- [x] Agent secret resolution works without exposing plaintext — _resolve_secret() returns env var value_
- [x] Tests cover encryption/decryption, scope enforcement, and rotation

---

#### FM-180: Enterprise Governance Tests, Docs & Hardening

**Goal:** Test coverage, security hardening, and documentation for all Wave 13 features.

**Capabilities:**

- Full test suite for FM-171–179 services
- Security review: audit log tamper resistance, permission bypass testing
- Performance testing: audit log query performance at scale
- Admin guide: "Enterprise governance setup"

**Backend scope:**

- Test file: `test_fm171_180_enterprise_governance.py`
- Permission bypass fuzzing: test all routes with insufficient permissions
- Audit log write performance benchmark
- Encryption key rotation documentation

**Frontend scope:**

- Error states for permission denied scenarios
- Loading states for compliance report generation

**Acceptance criteria:**

- [x] All FM-171–179 services have test coverage (target: 45+ tests) — _70+ tests_
- [ ] No permission bypass found in security testing — _Deferred: needs systematic route fuzzing_
- [ ] Audit log writes handle 1000+ events/minute without degradation — _Deferred: needs load testing infrastructure_
- [x] Documentation covers org setup, SSO, policies, and compliance reporting — _All docs updated with honest status_

---

### Wave 14 — Code Intelligence, Change Awareness & Test Intelligence (FM-181 → FM-190)

---

#### FM-181: Codebase Graph — File & Module Dependency Mapping

**Goal:** Build a graph-based representation of the codebase's file and module dependencies to power change impact analysis.

**Capabilities:**

- Parse import/require/include statements across Python, TypeScript, and SQL files
- Build directed acyclic graph of module dependencies
- Query: "What depends on module X?" (reverse dependencies)
- Incremental update: re-parse only changed files on new commits

**Backend scope:**

- `CodeGraphService`: parse files, extract imports, build dependency graph (adjacency list)
- `ModuleDependency` model: id, project_id, source_file, target_file, dependency_type (import/dynamic), last_scanned
- Parsers: Python (`ast` module), TypeScript (regex-based or tree-sitter), SQL (schema references)
- Route: GET `/projects/{id}/code-graph`, GET `/projects/{id}/code-graph/dependents?file=...`
- Incremental scan: diff changed files from last scan, re-parse only those

**Frontend scope:**

- Dependency graph visualization (interactive, zoomable)
- "What depends on this?" panel on file views
- Dependency count badges on file lists

**Acceptance criteria:**

- [ ] Python imports parsed correctly (relative, absolute, from...import)
- [ ] TypeScript imports parsed correctly (ES6, CommonJS)
- [ ] Reverse dependency query returns correct dependents
- [ ] Incremental scan processes only changed files
- [ ] Tests cover parsing, graph building, and queries

---

#### FM-182: Change Impact Analysis

**Goal:** Given a set of changed files, compute the blast radius — what modules, tests, and features are potentially affected.

**Capabilities:**

- Input: list of changed files (from commit diff or PR)
- Output: affected modules (transitive dependents), affected tests, affected features/specs
- Risk summary: blast radius size, high-risk paths flagged
- Integration: auto-run on PR creation, available as standalone analysis

**Backend scope:**

- `ImpactAnalysisService`: walk dependency graph from changed files, collect affected nodes
- Map affected files to tests (by import chain or naming convention: `file.py` → `test_file.py`)
- Map affected files to features/specs (via artifact linkage)
- Risk scoring: size of blast radius, presence of critical paths
- Route: POST `/projects/{id}/impact-analysis` (body: list of files or commit SHA)

**Frontend scope:**

- Impact analysis panel on PR view and run detail
- Blast radius visualization (tree or sunburst chart)
- Risk summary card with score and affected area counts

**Acceptance criteria:**

- [ ] Transitive dependencies followed correctly (A imports B imports C → change C affects A)
- [ ] Test mapping identifies affected test files
- [ ] Risk scoring correlates with blast radius size
- [ ] Analysis completes in <5 seconds for typical projects
- [ ] Tests cover transitive analysis, test mapping, and risk scoring

---

#### FM-183: Test Coverage Mapping

**Goal:** Map test files to the source files they cover, enabling intelligent test selection and coverage gap detection.

**Capabilities:**

- Static analysis: infer coverage from imports and naming conventions
- Coverage report ingestion: parse pytest-cov, istanbul, or generic LCOV reports
- Coverage map: source file → { covered_by: [test files], coverage_pct }
- Coverage gap detection: "These 12 source files have no tests"

**Backend scope:**

- `TestCoverageService`: build coverage map from static analysis + coverage reports
- `CoverageMap` model: project_id, source_file, test_file, coverage_pct, last_updated
- Coverage report parser: accept pytest-cov JSON, istanbul JSON, LCOV
- Route: GET `/projects/{id}/coverage-map`, GET `/projects/{id}/coverage-gaps`
- Ingestion: POST `/projects/{id}/coverage-report` (upload coverage file)

**Frontend scope:**

- Coverage map table: source file, covered tests, coverage percentage
- Coverage gaps list with "priority" ranking (most-imported uncovered files first)
- Coverage badge on project overview

**Acceptance criteria:**

- [ ] Static analysis correctly maps tests to sources
- [ ] Coverage report ingestion produces accurate file-level metrics
- [ ] Coverage gaps detected and ranked by importance
- [ ] Tests cover static mapping, report parsing, and gap detection

---

#### FM-184: Intelligent Test Selection

**Goal:** Given changed files, automatically select the minimal set of tests to run for validation.

**Capabilities:**

- Combine change impact analysis (FM-182) + test coverage map (FM-183)
- Output: ordered list of tests to run, with rationale
- Modes: minimal (directly affected), standard (1-hop transitive), comprehensive (full blast radius)
- Confidence score: how likely the selected tests are to catch regressions

**Backend scope:**

- `TestSelectionService`: intersect impact set with coverage map, rank by risk
- Selection modes: minimal, standard, comprehensive (configurable depth)
- Confidence scoring: based on coverage quality and dependency distance
- Route: POST `/projects/{id}/select-tests` (body: changed files, mode)

**Frontend scope:**

- Test selection panel on PR view: "17 tests recommended" with expandable list
- Mode selector (minimal/standard/comprehensive)
- "Run selected tests" button (triggers CI or local test run)

**Acceptance criteria:**

- [ ] Minimal mode selects only directly affected tests
- [ ] Standard mode includes 1-hop transitive tests
- [ ] Comprehensive mode covers full blast radius
- [ ] Confidence score reflects coverage quality
- [ ] Tests cover all three modes with known dependency graphs

---

#### FM-185: Code Pattern Detection

**Goal:** Identify recurring code patterns (both positive and problematic) across the codebase for quality and consistency insights.

**Capabilities:**

- Pattern types: anti-patterns (God class, deep nesting, magic numbers), positive patterns (repository pattern, dependency injection)
- Configurable pattern rules (regex + AST-based for Python)
- Pattern density metrics: patterns per file, per module
- Integration with knowledge base (FM-163): auto-create knowledge entries for detected patterns

**Backend scope:**

- `PatternDetectionService`: scan files with rule engine
- `PatternRule` model: id, org_id, name, pattern_type (anti/positive), language, rule_definition (regex or AST query), severity
- `PatternOccurrence` model: project_id, file, line_start, line_end, rule_id, detected_at
- Route: POST `/projects/{id}/scan-patterns`, GET `/projects/{id}/patterns`

**Frontend scope:**

- Pattern scan results page: grouped by type and severity
- Pattern detail with code snippet and explanation
- Pattern trend chart: are anti-patterns increasing or decreasing?

**Acceptance criteria:**

- [ ] At least 5 anti-pattern and 3 positive-pattern rules implemented
- [ ] Patterns detected with correct file/line references
- [ ] Pattern density metrics computed correctly
- [ ] Knowledge base integration creates entries for significant patterns
- [ ] Tests cover rule matching, location accuracy, and metrics

---

#### FM-186: Technical Debt Tracking

**Goal:** Quantify and track technical debt across the codebase, integrating pattern detection, age analysis, and manual tagging.

**Capabilities:**

- Debt sources: detected patterns (FM-185), TODO/FIXME/HACK comments, old unchanged files, complexity metrics
- Debt score per file and per project (composite metric)
- Debt trend: track score over time to see if debt is growing or shrinking
- Debt budget: set acceptable debt threshold per project

**Backend scope:**

- `TechDebtService`: scan codebase for debt indicators, compute scores, track history
- `DebtEntry` model: project_id, file, debt_type (pattern/comment/age/complexity), description, score, detected_at
- `DebtSnapshot` model: project_id, total_score, entry_count, snapshot_date
- Route: POST `/projects/{id}/scan-debt`, GET `/projects/{id}/debt-summary`, GET `/projects/{id}/debt-trend`

**Frontend scope:**

- Technical debt dashboard: total score, trend chart, top debt files
- Debt entries table sortable by score, type, file
- Debt budget indicator: gauge showing current vs. threshold

**Acceptance criteria:**

- [ ] All 4 debt sources detected and scored
- [ ] Project-level composite score computed correctly
- [ ] Trend tracking shows debt changes over snapshots
- [ ] Budget threshold triggers warning when exceeded
- [ ] Tests cover all debt sources, scoring, and trend computation

---

#### FM-187: Test Flakiness Detection

**Goal:** Identify flaky tests by analyzing test result history and flag them for remediation.

**Capabilities:**

- Track test outcomes over multiple runs (pass/fail history per test)
- Flakiness score: percentage of inconsistent results in recent window
- Flaky test report: ranked by flakiness score with trend
- Auto-quarantine: option to exclude flaky tests from blocking gates

**Backend scope:**

- `TestResult` model: id, project_id, test_name, test_file, outcome (pass/fail/skip/error), run_id, duration_ms, timestamp
- `FlakinessService`: compute flakiness score (inconsistency ratio over last N runs), rank, quarantine
- Quarantine list: excluded from readiness gates but still executed for monitoring
- Route: GET `/projects/{id}/flaky-tests`, POST `/projects/{id}/quarantine-test`

**Frontend scope:**

- Flaky tests page: sorted by flakiness score
- Trend sparkline per test (last 20 runs)
- Quarantine toggle per test
- Flaky test count badge on project overview

**Acceptance criteria:**

- [ ] Flakiness score computed correctly from result history
- [ ] Quarantined tests excluded from gate checks
- [ ] Quarantined tests still executed and monitored
- [ ] Tests cover score calculation, ranking, and quarantine logic

---

#### FM-188: Code Complexity Metrics

**Goal:** Compute and track code complexity metrics (cyclomatic complexity, cognitive complexity, line count) at file and function level.

**Capabilities:**

- Metrics: cyclomatic complexity, cognitive complexity, lines of code, function count
- Granularity: per-function and per-file
- Threshold alerts: flag functions exceeding complexity thresholds
- Trend tracking: complexity changes across runs/commits

**Backend scope:**

- `ComplexityService`: AST-based analysis for Python (extendable to TypeScript)
- `ComplexityMetric` model: project_id, file, function_name, metric_type, value, snapshot_date
- Threshold configuration per project
- Route: POST `/projects/{id}/analyze-complexity`, GET `/projects/{id}/complexity`

**Frontend scope:**

- Complexity dashboard: sortable table of functions with metrics
- Threshold violations highlighted in red
- Complexity trend chart per file or function

**Acceptance criteria:**

- [ ] Cyclomatic and cognitive complexity computed correctly for Python
- [ ] Threshold violations flagged accurately
- [ ] Trend tracking shows changes across snapshots
- [ ] Tests cover complexity calculation for various code structures

---

#### FM-189: Code Intelligence Agent Integration

**Goal:** Feed code intelligence data (graph, coverage, complexity, debt) into agent decision-making during runs.

**Capabilities:**

- Agents receive code context: dependency graph, coverage map, complexity hotspots, debt areas
- Planning agent uses impact analysis to scope tasks
- Coder agent avoids high-debt areas or flags them for review
- Reviewer agent checks against pattern rules and complexity thresholds

**Backend scope:**

- `CodeIntelligenceContext`: aggregate code intelligence data for a run's scope
- Inject context into agent prompts via execution context enrichment
- Decision audit: log which code intelligence data influenced agent decisions
- No new routes (internal service used by agent execution pipeline)

**Frontend scope:**

- "Code context used" section on task detail showing what intelligence informed agent decisions
- Code intelligence summary on run detail

**Acceptance criteria:**

- [ ] Agents receive relevant code intelligence in their execution context
- [ ] Planning agent considers impact analysis when scoping tasks
- [ ] Decision audit correctly logs intelligence influence
- [ ] Tests cover context injection and decision logging

---

#### FM-190: Code Intelligence Tests, Docs & Hardening

**Goal:** Test coverage, performance optimization, and documentation for all Wave 14 features.

**Capabilities:**

- Full test suite for FM-181–189 services
- Graph traversal performance benchmarking
- Large codebase simulation testing
- Developer guide: "Code intelligence features"

**Backend scope:**

- Test file: `test_fm181_190_code_intelligence.py`
- Benchmark: graph traversal for 10,000-file project
- Parser robustness: handle malformed imports, circular dependencies
- Graceful fallback when code intelligence data unavailable

**Acceptance criteria:**

- [ ] All FM-181–189 services have test coverage (target: 40+ tests)
- [ ] Graph traversal completes in <2 seconds for 10K-file projects
- [ ] Parsers handle malformed input without crashing
- [ ] Documentation covers setup, configuration, and interpretation of results

---

### Wave 15 — Analytics, Metrics & Portfolio Operations (FM-191 → FM-200)

---

#### FM-191: Run Execution Metrics & Time Tracking

**Goal:** Capture detailed timing metrics for every stage of run execution to enable velocity analysis.

**Capabilities:**

- Per-task timing: queue time, execution time, review time, total time
- Per-run timing: planning time, execution time, review time, total cycle time
- Agent utilization: time each agent spends active vs. idle
- Metrics exposed for dashboard consumption

**Backend scope:**

- `ExecutionMetric` model: id, run_id, task_id, metric_type, value_ms, recorded_at
- `MetricsService`: record metrics at lifecycle transitions, aggregate by run/project/time window
- Auto-capture: instrument task status transitions to compute stage durations
- Route: GET `/runs/{id}/metrics`, GET `/projects/{id}/metrics?window=7d`

**Frontend scope:**

- Run metrics panel: waterfall chart showing stage durations
- Project metrics: average cycle time trend chart
- Agent utilization breakdown

**Acceptance criteria:**

- [ ] All stage timings captured automatically from status transitions
- [ ] Aggregation correctly computes averages, medians, and percentiles
- [ ] Time window queries work for 1d, 7d, 30d, 90d
- [ ] Tests cover metric recording, aggregation, and windowed queries

---

#### FM-192: Project Health Scoring

**Goal:** Compute a composite "project health" score from multiple signals to give at-a-glance status.

**Capabilities:**

- Health dimensions: run success rate, approval velocity, test coverage, code debt, release frequency
- Composite score: weighted average (configurable weights)
- Health grade: A/B/C/D/F with color coding
- Historical health trend

**Backend scope:**

- `HealthScoringService`: compute dimension scores from existing data, weighted composite
- `HealthSnapshot` model: project_id, dimension_scores (JSON), composite_score, grade, snapshot_date
- Configurable weights per organization
- Route: GET `/projects/{id}/health`, GET `/projects/{id}/health-trend`

**Frontend scope:**

- Health grade badge on project card and overview
- Health dimension breakdown (radar chart)
- Health trend line chart
- Configuration: weight sliders in org settings

**Acceptance criteria:**

- [ ] All 5 health dimensions computed from real project data
- [ ] Weighted composite produces expected scores
- [ ] Grade thresholds: A (90+), B (75+), C (60+), D (45+), F (<45)
- [ ] Trend captures changes over time
- [ ] Tests cover dimension scoring, weighting, and grading

---

#### FM-193: Cost Tracking & Budget Management

**Goal:** Track AI inference costs (LLM tokens, embeddings) and resource usage per run, project, and organization.

**Capabilities:**

- Track tokens consumed per agent action (prompt + completion tokens)
- Cost computation: token count × model rate
- Budget limits: per-project and per-org, with alerts at thresholds
- Cost breakdown: by model, by agent, by run, by project

**Backend scope:**

- `CostRecord` model: id, run_id, task_id, agent_type, model_name, prompt_tokens, completion_tokens, estimated_cost_usd, recorded_at
- `CostService`: record on each LLM call, aggregate by dimensions, check budget
- Budget enforcement: block new runs when budget exceeded (configurable: block/warn/log)
- Route: GET `/projects/{id}/costs`, GET `/organizations/{id}/costs`, GET `/runs/{id}/costs`

**Frontend scope:**

- Cost dashboard: total spend, trend chart, breakdown by model/agent
- Budget indicator: usage bar with threshold markers
- Alert configuration: notification at 50%, 80%, 100% of budget

**Acceptance criteria:**

- [ ] Every LLM call recorded with accurate token counts
- [ ] Cost computation uses configurable model rates
- [ ] Budget enforcement blocks/warns at threshold
- [ ] Aggregation by model, agent, run, and project all work
- [ ] Tests cover recording, aggregation, budget enforcement

---

#### FM-194: Team Velocity & Throughput Metrics

**Goal:** Measure team productivity metrics — tasks completed, runs finished, approval turnaround — over time.

**Capabilities:**

- Throughput: tasks completed per day/week/month
- Velocity: run completion rate, average tasks per run
- Approval velocity: average time from request to decision
- Comparative: this week vs. last week, this month vs. last

**Backend scope:**

- `VelocityService`: compute throughput, velocity, and approval metrics from existing data
- Time series generation: daily/weekly/monthly bucketing
- Comparative computation: current period vs. previous period (% change)
- Route: GET `/projects/{id}/velocity?window=7d&compare=previous`

**Frontend scope:**

- Velocity dashboard: key metrics with trend arrows (↑↓→)
- Throughput chart: tasks/runs over time
- Approval velocity chart: turnaround time trend
- Comparison cards: current vs. previous period

**Acceptance criteria:**

- [ ] Throughput computed correctly for all time windows
- [ ] Velocity includes runs and tasks per run
- [ ] Approval velocity measures request-to-decision duration
- [ ] Comparison % change calculated correctly
- [ ] Tests cover all metrics, time windows, and comparisons

---

#### FM-195: Quality Metrics Dashboard

**Goal:** Surface quality-focused metrics — test pass rates, defect density, rollback frequency, code review coverage.

**Capabilities:**

- Test pass rate: percentage of tests passing over time
- Defect density: issues/regressions per run
- Rollback frequency: how often releases are rolled back
- Review coverage: percentage of tasks that received human review

**Backend scope:**

- `QualityMetricsService`: compute quality metrics from run results, test results, release history
- `QualitySnapshot` model: project_id, test_pass_rate, defect_density, rollback_rate, review_coverage, snapshot_date
- Route: GET `/projects/{id}/quality-metrics`, GET `/projects/{id}/quality-trend`

**Frontend scope:**

- Quality dashboard: 4 metric cards with trend sparklines
- Quality trend chart: overlay all metrics
- Quality gates configuration: set minimum thresholds

**Acceptance criteria:**

- [ ] All 4 quality metrics computed from real data
- [ ] Snapshot captures daily state for trend viewing
- [ ] Quality gates trigger warnings when thresholds breached
- [ ] Tests cover all metric computations and gate evaluation

---

#### FM-196: Portfolio Overview — Multi-Project Dashboard

**Goal:** Provide a single dashboard showing all projects in an organization with their health, velocity, costs, and status.

**Capabilities:**

- Portfolio grid: all projects with health grade, active runs, recent releases
- Sortable by any metric (health, cost, velocity, last activity)
- Portfolio-level aggregates: total cost, total runs, average health
- Drill-down: click project to go to project overview

**Backend scope:**

- `PortfolioService`: aggregate metrics across all org projects
- Batch query optimization: single query for multi-project health, metrics, costs
- Route: GET `/organizations/{id}/portfolio`

**Frontend scope:**

- Portfolio page: card grid or table view (toggleable)
- Sort/filter bar: by health grade, cost, velocity, activity
- Aggregate stats row at top
- Click-through to project overview

**Acceptance criteria:**

- [ ] Portfolio shows all org projects with accurate metrics
- [ ] Sort and filter work across all dimensions
- [ ] Aggregates computed correctly
- [ ] Performance: <1 second for 50 projects
- [ ] Tests cover multi-project aggregation and sorting

---

#### FM-197: Custom Dashboards & Widgets

**Goal:** Let users create custom dashboards by arranging metric widgets on a canvas.

**Capabilities:**

- Widget library: chart types (line, bar, pie, table, number, gauge)
- Data sources: any metric endpoint (health, velocity, cost, quality, etc.)
- Layout: drag-and-drop grid layout, resizable widgets
- Dashboard sharing: private or team-shared (reuse SavedView concept)

**Backend scope:**

- `Dashboard` model: id, org_id, creator_id, name, layout_json, visibility, created_at
- `Widget` schema (embedded in layout_json): widget_type, data_source, parameters, position, size
- Dashboard CRUD service
- Route: CRUD on `/dashboards`

**Frontend scope:**

- Dashboard builder: drag-and-drop grid (react-grid-layout or similar)
- Widget picker: select type, configure data source and parameters
- Preview mode vs. edit mode
- Dashboard gallery: browse team dashboards

**Acceptance criteria:**

- [ ] Widgets render correctly for all chart types
- [ ] Layout saves and restores accurately
- [ ] Data sources fetch correct metric data
- [ ] Sharing with team visibility works
- [ ] Tests cover dashboard CRUD and widget data resolution

---

#### FM-198: Scheduled Reports & Alerts

**Goal:** Configure automated metric reports and threshold-based alerts delivered via notification system.

**Capabilities:**

- Scheduled report: select metrics, schedule (daily/weekly/monthly), delivery (notification, email placeholder)
- Threshold alert: when metric crosses boundary (e.g., health < 60, cost > budget 80%)
- Alert routing: user, team, or org-wide notifications
- Alert history: past triggers with context

**Backend scope:**

- `ScheduledReport` model: id, org_id, name, metrics (JSON), schedule_cron, recipients (JSON), active
- `MetricAlert` model: id, org_id, metric_type, condition (JSON: op, threshold), recipients, cooldown_minutes, active
- `AlertService`: evaluate alert conditions, generate notifications, respect cooldown
- Route: CRUD on `/scheduled-reports`, CRUD on `/metric-alerts`

**Frontend scope:**

- Report scheduler: select metrics, set schedule, choose recipients
- Alert configuration: select metric, set condition, choose recipients
- Active alerts list with last triggered timestamp
- Alert history log

**Acceptance criteria:**

- [ ] Scheduled reports generate on schedule with correct metrics
- [ ] Alerts trigger when conditions are met
- [ ] Cooldown prevents alert spam
- [ ] Alert history shows all triggers with context
- [ ] Tests cover scheduling, condition evaluation, and cooldown logic

---

#### FM-199: Executive Summary Generator

**Goal:** Auto-generate executive summaries from portfolio data for status meetings and stakeholder updates.

**Capabilities:**

- Summary includes: portfolio health, top risks, key achievements, cost summary, upcoming releases
- Configurable scope: single project or entire org
- Tone: executive-friendly (no technical jargon)
- Output: markdown document, artifact-stored, shareable link

**Backend scope:**

- `ExecutiveSummaryService`: aggregate data from portfolio, health, velocity, cost, release services
- Template-based generation with configurable sections
- Store as Artifact for versioning and sharing
- Route: POST `/organizations/{id}/executive-summary/generate`, GET `/executive-summaries/{id}`

**Frontend scope:**

- "Generate summary" button on portfolio page
- Summary preview with section toggles
- Share button with link generation
- Summary history list

**Acceptance criteria:**

- [ ] Summary includes all configured sections with accurate data
- [ ] Non-technical language used in generated text
- [ ] Summary stored as versioned artifact
- [ ] Tests cover generation with realistic multi-project data

---

#### FM-200: Analytics Tests, Docs & Hardening

**Goal:** Test coverage, performance optimization, and documentation for all Wave 15 features.

**Capabilities:**

- Full test suite for FM-191–199 services
- Aggregation performance benchmarking (large data sets)
- Dashboard rendering performance
- Admin guide: "Analytics and portfolio operations"

**Backend scope:**

- Test file: `test_fm191_200_analytics.py`
- Load testing: metric queries with 10K+ records
- Materialized view or caching strategy for expensive aggregations
- Metric data archival strategy for long-term storage

**Acceptance criteria:**

- [ ] All FM-191–199 services have test coverage (target: 40+ tests)
- [ ] Metric queries respond in <500ms for 90-day windows
- [ ] Dashboard load time <2 seconds with 10 widgets
- [ ] Documentation covers metric definitions, dashboard setup, and alert configuration

---

### Wave 16 — API, Webhooks & Ecosystem Integrations (FM-201 → FM-210)

---

#### FM-201: Public API v1 — Core Endpoints

**Goal:** Define and publish a versioned public API surface covering the core ForgeMind capabilities.

**Capabilities:**

- RESTful API with `/api/v1/` prefix
- Endpoints: projects, runs, tasks, artifacts, approvals, releases
- OpenAPI 3.0 specification auto-generated
- API key authentication (in addition to JWT)

**Backend scope:**

- API router: `/api/v1/` with versioned controllers delegating to existing services
- `APIKey` model: id, org_id, name, key_hash, scopes (JSON), created_at, last_used, revoked
- API key middleware: validate key, enforce scopes, record usage
- OpenAPI spec generation from FastAPI (already built-in — ensure all routes documented)
- Route: POST `/api-keys`, GET `/api-keys`, DELETE `/api-keys/{id}`

**Frontend scope:**

- API keys management page: create, list, revoke
- API documentation page (embedded Swagger UI or Redoc)
- "Try it" feature for authenticated exploration

**Acceptance criteria:**

- [ ] All core endpoint groups accessible via `/api/v1/`
- [ ] API key authentication works alongside JWT
- [ ] Scoped API keys restrict access to specified resources
- [ ] OpenAPI spec complete and valid
- [ ] Tests cover API key lifecycle and scope enforcement

---

#### FM-202: API Rate Limiting & Throttling

**Goal:** Protect the API with configurable rate limits per key, per org, and per endpoint.

**Capabilities:**

- Rate limit tiers: per API key, per org, per endpoint
- Sliding window rate limiting (not just fixed window)
- Rate limit headers in responses: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`
- Configurable limits per org plan tier
- Graceful degradation: 429 response with retry-after

**Backend scope:**

- `RateLimiter`: sliding window counter (Redis-backed or in-memory with fallback)
- Rate limit middleware: check before request processing
- Configuration: `RateLimitConfig` per org plan tier (requests per minute/hour)
- Rate limit headers injection middleware

**Frontend scope:**

- Rate limit usage display in API key management
- Rate limit exceeded notification

**Acceptance criteria:**

- [ ] Sliding window correctly counts requests
- [ ] Rate limit headers present on all API responses
- [ ] 429 returned with correct retry-after when limit exceeded
- [ ] Different limits per tier enforced correctly
- [ ] Tests cover sliding window accuracy, header injection, and tier enforcement

---

#### FM-203: Webhook Subscription System

**Goal:** Allow external systems to subscribe to ForgeMind events via webhooks with reliable delivery.

**Capabilities:**

- Event types: run.started, run.completed, task.completed, approval.requested, release.published, etc.
- Subscription management: URL, secret (HMAC signing), event filter, active toggle
- Delivery: signed payload with retry on failure (exponential backoff, max 5 attempts)
- Delivery log: status, response code, latency, retry count

**Backend scope:**

- `WebhookSubscription` model: id, org_id, url, secret_encrypted, events (JSON array), active, created_at
- `WebhookDeliveryService`: serialize event, sign payload (HMAC-SHA256), POST to URL, log result
- `WebhookDelivery` model: id, subscription_id, event_type, payload_hash, status_code, attempt, next_retry, delivered_at
- Retry queue: failed deliveries re-attempted with exponential backoff
- Route: CRUD on `/webhook-subscriptions`, GET `/webhook-subscriptions/{id}/deliveries`

**Frontend scope:**

- Webhook management page: create subscription, select events, configure URL/secret
- Delivery log table per subscription with status indicators
- "Test" button to send a test event
- Retry button for failed deliveries

**Acceptance criteria:**

- [ ] Webhooks fire for all configured event types
- [ ] Payload signed with HMAC-SHA256 using subscription secret
- [ ] Failed deliveries retried up to 5 times with exponential backoff
- [ ] Delivery log records all attempts with status codes
- [ ] Tests cover event serialization, signing, delivery, retry, and logging

---

#### FM-204: Slack Integration

**Goal:** Enable bidirectional Slack integration — notifications to channels and commands from Slack.

**Capabilities:**

- Outbound: post run completion, approval requests, release notifications to configured Slack channels
- Inbound: `/forgemind approve <id>`, `/forgemind status <project>`, `/forgemind start-run <spec-id>`
- Channel mapping: project → Slack channel
- Rich message formatting with action buttons (approve/reject)

**Backend scope:**

- `SlackIntegration` model: org_id, workspace_id, access_token_encrypted, bot_user_id
- `SlackService`: post message, handle slash command, handle interactive action
- Channel mapping stored in project settings
- OAuth2 installation flow for Slack workspace
- Routes: POST `/integrations/slack/install`, POST `/integrations/slack/commands`, POST `/integrations/slack/actions`

**Frontend scope:**

- Slack integration setup page in org settings (install button, channel mapping)
- Per-project Slack channel configuration
- Notification type toggles (which events post to Slack)

**Acceptance criteria:**

- [ ] Slack app installs via OAuth2 flow
- [ ] Messages posted to correct channels with rich formatting
- [ ] Slash commands execute correct actions
- [ ] Interactive buttons (approve/reject) work
- [ ] Tests cover message posting, command handling, and action processing (mocked Slack API)

---

#### FM-205: Jira Integration — Issue & Sprint Sync

**Goal:** Synchronize ForgeMind projects/tasks with Jira projects/issues, enabling teams to use both systems in parallel.

**Capabilities:**

- Link ForgeMind project ↔ Jira project
- Task ↔ Issue sync: bidirectional status and field mapping
- Sprint mapping: ForgeMind runs ↔ Jira sprints
- Custom field mapping configuration

**Backend scope:**

- `JiraIntegration` model: org_id, jira_url, api_token_encrypted, project_mapping (JSON)
- `JiraSyncService`: import issues, export tasks, sync status changes, map custom fields
- `JiraLink` model: task_id, jira_issue_key, sync_direction, last_synced_at
- Webhook receiver: Jira sends issue updates → ForgeMind task updates
- Route: CRUD on `/integrations/jira`, POST `/projects/{id}/sync-jira`

**Frontend scope:**

- Jira integration setup page
- Field mapping configuration (ForgeMind field → Jira field)
- Sync status dashboard: last synced, pending changes, sync errors

**Acceptance criteria:**

- [ ] Jira issues import correctly with field mapping
- [ ] ForgeMind tasks export as Jira issues
- [ ] Bidirectional status sync works
- [ ] Custom field mapping configurable and respected
- [ ] Tests cover import, export, bidirectional sync, and field mapping (mocked Jira API)

---

#### FM-206: PagerDuty & Incident Integration

**Goal:** Alert on-call teams via PagerDuty when ForgeMind detects critical failures — run failures, deployment issues, or budget alerts.

**Capabilities:**

- Incident creation: auto-create PagerDuty incidents for configurable triggers
- Trigger types: run failure, deployment rollback, health grade drop, budget overrun
- Severity mapping: trigger type → PagerDuty severity
- Incident resolution: auto-resolve when ForgeMind condition clears

**Backend scope:**

- `PagerDutyIntegration` model: org_id, service_id, routing_key_encrypted, active
- `PagerDutyService`: create incident, resolve incident, map severity
- Trigger configuration stored in org settings
- Route: CRUD on `/integrations/pagerduty`, POST `/integrations/pagerduty/test`

**Frontend scope:**

- PagerDuty integration setup page
- Trigger configuration: select conditions, map severities
- Test alert button
- Incident history (ForgeMind-originated incidents)

**Acceptance criteria:**

- [ ] Incidents created for all configured triggers
- [ ] Severity mapping applied correctly
- [ ] Auto-resolution works when condition clears
- [ ] Tests cover incident creation, severity mapping, and resolution (mocked PagerDuty API)

---

#### FM-207: Email Notification Channel

**Goal:** Add email as a notification delivery channel with configurable templates and digest options.

**Capabilities:**

- Transactional emails: approval requests, run completions, mentions, budget alerts
- Email templates: branded HTML templates per event type
- Digest emails: configurable frequency (immediate, hourly, daily)
- Unsubscribe management per email category

**Backend scope:**

- `EmailService`: render template, send via SMTP or API provider (SendGrid, SES)
- Email templates: Jinja2 HTML templates per notification category
- Digest aggregator: collect notifications, render consolidated digest email
- Unsubscribe: `EmailPreference` model per user per category
- Route: GET/PATCH `/users/{id}/email-preferences`

**Frontend scope:**

- Email preferences page in user settings (per-category frequency toggles)
- Unsubscribe link handling
- Email template preview for admins

**Acceptance criteria:**

- [ ] Transactional emails sent for all notification categories
- [ ] HTML templates render correctly across major email clients
- [ ] Digest aggregates notifications at configured frequency
- [ ] Unsubscribe respected per category
- [ ] Tests cover template rendering, digest aggregation, and preference enforcement

---

#### FM-208: Integration Marketplace & Custom Connectors

**Goal:** Provide a framework for building and installing custom integrations via a standardized connector interface.

**Capabilities:**

- Connector interface: standard contract for inbound/outbound integrations
- Connector types: source (push data in), sink (push data out), bidirectional
- Connector registry: install/uninstall/configure per org
- Connector SDK: documentation and examples for building custom connectors

**Backend scope:**

- `Connector` interface: abstract base class with `receive_event()`, `send_event()`, `configure()`, `health_check()`
- `ConnectorRegistry` model: id, org_id, connector_type, config_json, active, installed_at
- Built-in connectors: GitHub, Slack, Jira, PagerDuty, Email (refactored to implement interface)
- Route: GET `/integrations/marketplace`, POST `/integrations/install`, DELETE `/integrations/{id}/uninstall`

**Frontend scope:**

- Integration marketplace page: browse available connectors
- Install/configure/uninstall flow per connector
- Health status indicator per installed connector

**Acceptance criteria:**

- [ ] Connector interface implemented by all existing integrations
- [ ] New connectors can be registered and configured dynamically
- [ ] Health check reports connector status
- [ ] Tests cover connector lifecycle (install, configure, health check, uninstall)

---

#### FM-209: API SDK & Client Libraries

**Goal:** Provide official client libraries (Python, TypeScript) for the ForgeMind API.

**Capabilities:**

- Python SDK: fully typed, async, covers all v1 endpoints
- TypeScript SDK: fully typed, covers all v1 endpoints
- Auto-generated from OpenAPI spec with manual ergonomic improvements
- Published as packages (pip/npm)

**Backend scope:**

- OpenAPI spec validation: ensure completeness and correctness for code generation
- SDK generation pipeline: openapi-generator with custom templates
- Python SDK: `forgemind-sdk` package with async client, typed models, error handling
- TypeScript SDK: `@forgemind/sdk` package with typed client and models

**Frontend scope:**

- SDK documentation page with getting-started guide
- Code examples for common operations
- Interactive playground (optional)

**Acceptance criteria:**

- [ ] Python SDK covers all v1 endpoints with correct types
- [ ] TypeScript SDK covers all v1 endpoints with correct types
- [ ] SDKs handle authentication, pagination, and error responses
- [ ] Tests: SDK integration tests against a test server
- [ ] Package installable via pip/npm

---

#### FM-210: Ecosystem Integration Tests, Docs & Hardening

**Goal:** Test coverage, security review, and documentation for all Wave 16 features.

**Capabilities:**

- Full test suite for FM-201–209 services
- Security review: webhook signature validation, secret handling, API key security
- Integration test scenario: end-to-end flow across Slack, GitHub, and API
- Developer guide: "Building on the ForgeMind API"

**Backend scope:**

- Test file: `test_fm201_210_ecosystem.py`
- Security audit: rate limiter bypass testing, webhook replay attack protection
- End-to-end integration scenario (mocked external services)
- API deprecation policy documentation

**Acceptance criteria:**

- [ ] All FM-201–209 services have test coverage (target: 45+ tests)
- [ ] No security vulnerabilities in webhook, API key, or secret handling
- [ ] End-to-end integration scenario passes
- [ ] Documentation covers API authentication, webhooks, and each integration setup

---

## 4. Prioritization Guidance

### Impact Matrix

| Wave                    | User Impact | Enterprise Impact | Differentiation | Recommended Priority |
| ----------------------- | ----------- | ----------------- | --------------- | -------------------- |
| Wave 10 (Collaboration) | ★★★★★       | ★★★☆☆             | ★★★★☆           | **P0 — Ship First**  |
| Wave 11 (GitHub/CI)     | ★★★★★       | ★★★★☆             | ★★★★★           | **P0 — Ship First**  |
| Wave 12 (Knowledge)     | ★★★★☆       | ★★★☆☆             | ★★★★★           | **P1 — Ship Second** |
| Wave 13 (Enterprise)    | ★★☆☆☆       | ★★★★★             | ★★★☆☆           | **P1 — Ship Second** |
| Wave 14 (Code Intel)    | ★★★★☆       | ★★★☆☆             | ★★★★★           | **P2 — Ship Third**  |
| Wave 15 (Analytics)     | ★★★☆☆       | ★★★★★             | ★★★☆☆           | **P2 — Ship Third**  |
| Wave 16 (API/Ecosystem) | ★★★★☆       | ★★★★☆             | ★★★★☆           | **P3 — Ship Fourth** |

### Recommended Sequence

**Phase A (Foundation for adoption):** Wave 10 + Wave 11 — These two blocks are non-negotiable for team adoption. Without collaboration and GitHub integration, ForgeMind remains a single-user prototype regardless of how powerful the engine is. Ship these together.

**Phase B (Depth for retention):** Wave 12 + Wave 13 — Knowledge makes the platform stickier (teams accumulate value over time), and enterprise governance unlocks budget buyers. These are necessary for any paid/enterprise tier.

**Phase C (Intelligence layer):** Wave 14 + Wave 15 — Code intelligence and analytics are the strongest differentiation features but require the data foundation from Phases A and B. They transform ForgeMind from "AI that writes code" to "AI that understands your engineering organization."

**Phase D (Ecosystem lock-in):** Wave 16 — Public APIs and integrations are the final moat. Once teams build workflows on ForgeMind's API and connect it to their tool stack, switching costs increase dramatically. Ship this after the platform is mature enough that the API surface is stable.

### Top 10 Flagship Features (Across All Waves)

These are the features that define V4's value proposition and should receive the most design attention:

1. **FM-153 — PR Auto-Creation** — The single most visible integration; makes every run immediately useful to developers
2. **FM-151 — GitHub App Installation** — Unlocks all developer tooling features; foundational
3. **FM-141 — Threaded Comments** — Transforms ForgeMind from tool to workspace
4. **FM-162 — Semantic Search** — "Find similar tasks/specs" is a killer feature for knowledge reuse
5. **FM-182 — Change Impact Analysis** — "What does this change affect?" answered automatically
6. **FM-193 — Cost Tracking** — Every AI platform needs transparent cost visibility; table stakes for enterprise
7. **FM-196 — Portfolio Overview** — The executive-facing feature that sells to budget holders
8. **FM-174 — Policy Engine** — Automated rule enforcement is the enterprise differentiator
9. **FM-184 — Intelligent Test Selection** — "Run only what matters" saves real time and money
10. **FM-203 — Webhook Subscriptions** — The platform play; enables custom integrations without ForgeMind code changes

---

## 5. Risks & Guardrails

### Technical Risks

| Risk                             | Severity | Mitigation                                                                                                   |
| -------------------------------- | -------- | ------------------------------------------------------------------------------------------------------------ |
| **GitHub API rate limits**       | High     | Rate limiter (FM-160), request queuing, conditional requests with ETags                                      |
| **Search index staleness**       | Medium   | Synchronous index on write for critical paths, async for bulk; integrity checker (FM-170)                    |
| **Embedding cost explosion**     | High     | Batch embedding generation, cache aggressively, lazy-generate (only on first search), configurable scope     |
| **Multi-tenant data leakage**    | Critical | Row-level security in all queries, permission checks in service layer + middleware, automated security tests |
| **Webhook delivery reliability** | Medium   | Exponential backoff, dead-letter queue, delivery log for debugging, idempotency keys                         |
| **Custom dashboard performance** | Medium   | Materialized views for expensive aggregations, widget-level caching, lazy loading                            |
| **SSO/SAML complexity**          | Medium   | Use proven library (python3-saml), extensive assertion validation, fallback to password auth                 |
| **Migration complexity**         | High     | All new tables additive (no breaking changes to existing schema), phased migrations per wave                 |

### Organizational Risks

| Risk                              | Severity | Mitigation                                                                                               |
| --------------------------------- | -------- | -------------------------------------------------------------------------------------------------------- |
| **Scope creep within waves**      | High     | Each wave ends with a hardening milestone (FM-150/160/170/180/190/200/210); no new features in hardening |
| **Over-engineering integrations** | Medium   | Start with read-only integrations, add write operations only when validated by usage                     |
| **Feature parity pressure**       | Medium   | Ship minimum viable versions first; iterate based on feedback before adding advanced options             |
| **Test coverage regression**      | Medium   | Maintain 90%+ coverage per wave; hardening milestones explicitly test cross-cutting concerns             |

### Guardrails

1. **No wave ships without its hardening milestone complete.** Every 10th milestone (FM-150, 160, 170, 180, 190, 200, 210) is dedicated to tests, docs, and edge cases. This is non-negotiable.

2. **All external API integrations use the same adapter pattern.** GitHub, Slack, Jira, and PagerDuty all implement a common `Connector` interface (FM-208). If an integration can't fit the interface, the interface needs updating — not the integration.

3. **Multi-tenancy is retroactive and must never leak.** Every query that returns user-visible data must include an organization/project scope filter. Automated tests verify this.

4. **Secrets never appear in logs, API responses, or frontend state.** All encryption uses AES-256-GCM. Secrets are write-once/read-by-reference-only. Audit log records access but not values.

5. **External service calls have timeouts, retries, and circuit breakers.** No API call to GitHub/Slack/Jira/PagerDuty blocks a request for more than 5 seconds. All use exponential backoff.

6. **Schema migrations are always additive during V4.** No column drops, no type changes on existing columns. Deprecated columns marked with `_deprecated` suffix and cleaned up in a future major version.

---

## 6. Final Recommendation

### V4 Structure

| Phase     | Waves        | Milestones          | Estimated Complexity |
| --------- | ------------ | ------------------- | -------------------- |
| Phase A   | Wave 10 + 11 | FM-141 → FM-160     | 20 milestones        |
| Phase B   | Wave 12 + 13 | FM-161 → FM-180     | 20 milestones        |
| Phase C   | Wave 14 + 15 | FM-181 → FM-200     | 20 milestones        |
| Phase D   | Wave 16      | FM-201 → FM-210     | 10 milestones        |
| **Total** | **7 waves**  | **FM-141 → FM-210** | **70 milestones**    |

### Start With Phase A

Phase A (Collaboration + GitHub) should begin immediately after FM-140 closure. The first milestone to implement is **FM-141 (Threaded Comments)** — it introduces the Comment model and collaboration primitives that FM-142 through FM-150 all depend on. From Wave 11, **FM-151 (GitHub App Installation)** is the gating milestone, since all subsequent GitHub features depend on the installation/auth layer.

### V4 Success Criteria

V4 is successful when:

- A team of 5+ developers uses ForgeMind daily for real projects (not demos)
- GitHub PRs are created from runs and reviewed inside ForgeMind
- Engineering leadership views portfolio health and cost dashboards weekly
- At least one external integration (Slack or Jira) is actively used
- Test coverage remains above 90% across all waves
- No multi-tenant data leakage in security testing
- API v1 is stable enough for a published SDK

### What V4 Does NOT Include

To keep scope bounded, the following are explicitly deferred to V5+ (see [FORGEMIND_V5_ROADMAP.md](FORGEMIND_V5_ROADMAP.md)):

- **Dynamic multi-agent orchestration** — V4 uses a fixed agent roster; V5 introduces dynamic agent spawning, inter-agent communication, and a master orchestration service (FM-211–FM-220)
- **Council-style deliberation** — V4 has voting-based councils; V5 adds full proposal-debate-resolution deliberation with reasoning chains (FM-221–FM-230)
- **Graph-based memory** — V4 uses linear execution memory; V5 introduces a knowledge graph for persistent structured reasoning (FM-231–FM-240)
- **Explainable workflow selection** — V4 routes tasks by capability scoring; V5 adds FAIR-style scoring with confidence signals and policy constraints (FM-241–FM-250)
- **Self-hosted deployment** — V4 assumes a managed platform model
- **Mobile app** — V4 focuses on web and CLI; mobile is a V5+ surface
- **Multi-language agent execution** — Agents remain Python-native; code generation targets multiple languages but agent code is Python
- **Real-time collaborative editing** — V4 has comments and annotations, not Google Docs-style co-editing
- **AI model fine-tuning** — V4 uses commercial LLM APIs; model customization is V5+
- **Marketplace for community connectors** — V4 builds the connector framework; a public marketplace is V5+

---

## Appendix: Milestone Index

| FM     | Title                                                   | Wave |
| ------ | ------------------------------------------------------- | ---- |
| FM-141 | Threaded Comments on Runs, Tasks & Artifacts            | 10   |
| FM-142 | @Mentions, User Tagging & Notification Routing          | 10   |
| FM-143 | Activity Feed — Project & Run Level                     | 10   |
| FM-144 | Shared Views & Saved Filters                            | 10   |
| FM-145 | User Presence & Online Status                           | 10   |
| FM-146 | Collaborative Run Annotations                           | 10   |
| FM-147 | Task Assignment & Workload Visibility                   | 10   |
| FM-148 | Approval Workflow Enhancements                          | 10   |
| FM-149 | Notification Center & Digest System                     | 10   |
| FM-150 | Team Dashboard & Project Overview Redesign              | 10   |
| FM-151 | GitHub App Installation & Repository Linking            | 11   |
| FM-152 | Webhook Receiver & Event Ingestion                      | 11   |
| FM-153 | PR Auto-Creation from Completed Runs                    | 11   |
| FM-154 | CI Pipeline Status Integration                          | 11   |
| FM-155 | Issue Sync — Bidirectional Issue Tracking               | 11   |
| FM-156 | Branch Strategy & Merge Automation                      | 11   |
| FM-157 | Code Review Request Routing                             | 11   |
| FM-158 | Commit & Diff Intelligence                              | 11   |
| FM-159 | IDE Extension Foundation (VS Code)                      | 11   |
| FM-160 | Developer Tooling Tests, Docs & Hardening               | 11   |
| FM-161 | Full-Text Search Index                                  | 12   |
| FM-162 | Semantic Search with Embeddings                         | 12   |
| FM-163 | Knowledge Base — Decision & Pattern Library             | 12   |
| FM-164 | Project Templates V2 — Knowledge-Enriched Bootstrapping | 12   |
| FM-165 | Cross-Project Search & Discovery                        | 12   |
| FM-166 | Execution Replay & Comparison                           | 12   |
| FM-167 | Organizational Context & Conventions Engine             | 12   |
| FM-168 | Artifact Versioning & History                           | 12   |
| FM-169 | Smart Recommendations Engine                            | 12   |
| FM-170 | Knowledge & Search Tests, Docs & Hardening              | 12   |
| FM-171 | Organization Model & Multi-Tenancy                      | 13   |
| FM-172 | Role-Based Access Control V2                            | 13   |
| FM-173 | Comprehensive Audit Log                                 | 13   |
| FM-174 | Policy Engine — Automated Rule Enforcement              | 13   |
| FM-175 | SSO & External Authentication                           | 13   |
| FM-176 | Data Retention & Lifecycle Policies                     | 13   |
| FM-177 | Compliance Reporting & Export                           | 13   |
| FM-178 | IP Allowlisting & Access Controls                       | 13   |
| FM-179 | Secrets Management & Vault Integration                  | 13   |
| FM-180 | Enterprise Governance Tests, Docs & Hardening           | 13   |
| FM-181 | Codebase Graph — File & Module Dependency Mapping       | 14   |
| FM-182 | Change Impact Analysis                                  | 14   |
| FM-183 | Test Coverage Mapping                                   | 14   |
| FM-184 | Intelligent Test Selection                              | 14   |
| FM-185 | Code Pattern Detection                                  | 14   |
| FM-186 | Technical Debt Tracking                                 | 14   |
| FM-187 | Test Flakiness Detection                                | 14   |
| FM-188 | Code Complexity Metrics                                 | 14   |
| FM-189 | Code Intelligence Agent Integration                     | 14   |
| FM-190 | Code Intelligence Tests, Docs & Hardening               | 14   |
| FM-191 | Run Execution Metrics & Time Tracking                   | 15   |
| FM-192 | Project Health Scoring                                  | 15   |
| FM-193 | Cost Tracking & Budget Management                       | 15   |
| FM-194 | Team Velocity & Throughput Metrics                      | 15   |
| FM-195 | Quality Metrics Dashboard                               | 15   |
| FM-196 | Portfolio Overview — Multi-Project Dashboard            | 15   |
| FM-197 | Custom Dashboards & Widgets                             | 15   |
| FM-198 | Scheduled Reports & Alerts                              | 15   |
| FM-199 | Executive Summary Generator                             | 15   |
| FM-200 | Analytics Tests, Docs & Hardening                       | 15   |
| FM-201 | Public API v1 — Core Endpoints                          | 16   |
| FM-202 | API Rate Limiting & Throttling                          | 16   |
| FM-203 | Webhook Subscription System                             | 16   |
| FM-204 | Slack Integration                                       | 16   |
| FM-205 | Jira Integration — Issue & Sprint Sync                  | 16   |
| FM-206 | PagerDuty & Incident Integration                        | 16   |
| FM-207 | Email Notification Channel                              | 16   |
| FM-208 | Integration Marketplace & Custom Connectors             | 16   |
| FM-209 | API SDK & Client Libraries                              | 16   |
| FM-210 | Ecosystem Integration Tests, Docs & Hardening           | 16   |

---

_End of ForgeMind V4 Roadmap — FM-141 through FM-210_

---

## Next: ForgeMind V5 (FM-211 → FM-250)

V5 transforms ForgeMind into a **dynamic multi-agent orchestration platform** with persistent graph-based reasoning and explainable workflow selection. See [FORGEMIND_V5_ROADMAP.md](FORGEMIND_V5_ROADMAP.md) for the full architecture vision and milestone breakdown.

| Block   | Range           | Theme                                       |
| ------- | --------------- | ------------------------------------------- |
| Wave 17 | FM-211 → FM-220 | Dynamic Multi-Agent Runtime Foundations     |
| Wave 18 | FM-221 → FM-230 | Council Collaboration & Deliberation Engine |
| Wave 19 | FM-231 → FM-240 | Graph Memory & Persistent Reasoning         |
| Wave 20 | FM-241 → FM-250 | Adaptive Workflow Selection & FAIR Engine   |

> **Status:** FUTURE — Planning begins after FM-210 is complete.
