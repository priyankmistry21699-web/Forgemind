# FM-140 — Tests, Docs & Hardening

## Goal

Test coverage, lint validation, and documentation for FM-131–139.

## What Was Implemented

- 39 tests across 8 test classes in `test_fm131_140_release_ops.py`
  - TestReleasePackageService (7 tests)
  - TestEnvironmentService (4 tests)
  - TestDeploymentReadiness (2 tests)
  - TestReleaseGates (4 tests)
  - TestRollbackReadiness (2 tests)
  - TestPostReleaseReport (3 tests)
  - TestOperationalTimeline (2 tests)
  - TestReleaseOpsRoutes (15 HTTP integration tests)
- Alembic migration `0025_add_release_ops_tables` (3 tables: release_packages, deployment_environments, release_gate_results)
- Model registration in `db/base.py`, route registration in `router.py`
- Ruff lint clean (9 auto-fixed issues)
- Full regression: **730 tests passing** (677 backend + 53 local)
- Bug fixes: 2 MissingGreenlet errors resolved with `await db.refresh()` in update functions

## Key Files

- `apps/api/tests/test_fm131_140_release_ops.py`
- `apps/api/alembic/versions/2026_04_06_0025_add_release_ops_tables.py`
- `apps/api/app/db/base.py`
- `apps/api/app/api/router.py`

## Status

✅ Complete
