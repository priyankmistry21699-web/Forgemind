# FM-070 — Code Ops Consolidation

## What was done

Consolidated all FM-061–069 enhancements with frontend pages, documentation updates, handoff response documents, and a comprehensive migration covering all schema changes.

## Files created

- `apps/web/app/dashboard/code-explorer/page.tsx` — File tree explorer with repo selector, split-panel directory browser, breadcrumb navigation, and file content viewer with language detection
- `apps/web/app/dashboard/reviews/[patchId]/page.tsx` — Review workspace with patch info header, diff viewer, file-level annotations with line ranges, suggestion rendering, and general review comments
- `apps/web/app/dashboard/sandbox/page.tsx` — Sandbox execution viewer with command runner, execution list, detail panel (stdout/stderr), and status badges
- `apps/api/alembic/versions/2026_03_31_0021_add_code_ops_enhancements.py` — Migration adding columns and enum types for FM-061–069
- `apps/api/tests/test_code_ops_enhanced.py` — 24 new tests covering all FM-061–069 enhancements
- `docs/agent-handoffs/FM-061-response.md` through `FM-070-response.md` — 10 handoff response documents

## Files modified

- `docs/ARCHITECTURE.md` — Updated: header date, test counts (303), model descriptions, new enums (5), API route descriptions, service table, schema table, migration list (21), test table, project structure counts
- `docs/MILESTONE_SUMMARY.md` — Updated: header date, current state description, milestone table (13 milestones), added FM-061–070 enhancement section with per-task details, updated total task count (70)
- `docs/TECHNICAL_DEBT.md` — Added 4 new items: TD-019 (static sandbox allowlist), TD-020 (local-only file explorer), TD-021 (template-based PR drafts), TD-022 (no container isolation for sandbox)

## Summary of FM-061–070 milestone

| Feature | Key Enhancement |
|---------|----------------|
| FM-061 | SyncStatus enum + 10 repo_connection columns + sync service/endpoints |
| FM-062 | File tree explorer with path traversal protection + frontend page |
| FM-063 | ChangeType enum + 5 artifact columns for code-to-artifact mapping |
| FM-064 | PatchFormat + ReadinessState enums + 5 patch_proposal columns |
| FM-065 | 4 change_review columns for inline annotations + review workspace page |
| FM-066 | BranchMode enum + 3 branch strategy columns on repo_connection |
| FM-067 | generate_pr_draft service + POST endpoint |
| FM-068 | check_approval_gate service + GET endpoint |
| FM-069 | Sandbox runner with allowlist + injection prevention + frontend page |
| FM-070 | 3 frontend pages + docs + migration + 24 tests |

**Migration 0021**: +10 cols on repo_connections, +5 on artifacts, +5 on patch_proposals, +4 on change_reviews, +4 on sandbox_executions; 5 new enum types
**Total tests**: 303 (all passing)
**Total features**: 70 across 13 milestones
