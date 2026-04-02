# FM-076 — CI/CD Pipeline and Quality Gates

## Status: ✅ Complete

## What was done

### 1. GitHub Actions CI Workflow (`.github/workflows/ci.yml`)
- **Trigger**: Push to `main` and pull requests targeting `main`
- **Concurrency**: Cancels duplicate runs for the same ref
- **Backend job** (Python 3.12):
  - pip install from `pyproject.toml` (with dev extras)
  - `ruff check .` — linting
  - `ruff format --check .` — format verification
  - `pytest --tb=short -q` — full test suite
- **Frontend job** (Node.js 20):
  - `npm ci` — deterministic dependency install
  - `npx tsc --noEmit` — TypeScript typecheck
  - `npm run lint` — ESLint via Next.js
  - `npm run build` — production build verification

### 2. Dependency Manifest Fixes (`apps/api/pyproject.toml`)
- Added `python-jose[cryptography]>=3.3.0` to main dependencies (was installed but undeclared)
- Added `aiosqlite>=0.20.0` to dev dependencies (required for test suite but undeclared)

### 3. Auto-Enrollment for RBAC Integrity
- **workspace_service.py**: `create_workspace()` now auto-enrolls the creator as `WorkspaceRole.OWNER` member
- **project_service.py**: `create_project()` now auto-enrolls the creator as `ProjectRole.LEAD` member
- **conftest.py**: `sample_project` fixture adds project lead enrollment (matches service behavior)
- Fixed 13 failing tests caused by FM-075 RBAC enforcement requiring membership records that didn't exist

### 4. Test Fixes
- Updated `test_members.py`: Use `OTHER_USER_ID` for add/update/remove tests (STUB_USER_ID is now auto-enrolled)
- Updated `test_collaboration_phase.py`: Fixed workspace permission tests and integration flow
- All assertions updated to account for auto-enrolled members in counts

## Files Created
- `.github/workflows/ci.yml`

## Files Modified
- `apps/api/pyproject.toml` — added missing dependencies
- `apps/api/app/services/workspace_service.py` — owner auto-enrollment
- `apps/api/app/services/project_service.py` — lead auto-enrollment
- `apps/api/tests/conftest.py` — sample_project fixture
- `apps/api/tests/test_members.py` — use OTHER_USER_ID
- `apps/api/tests/test_collaboration_phase.py` — fix RBAC and integration tests

## Test Results
- **346/346 passed** (0 failures, 92s)
