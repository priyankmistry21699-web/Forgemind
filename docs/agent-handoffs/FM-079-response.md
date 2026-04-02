# FM-079 — Monorepo Package Extraction

## Summary

Converted 4 of the 8 stub `packages/` directories into real, importable packages
with actual source code extracted from the codebase.

## Packages Created

### 1. `@forgemind/types` (packages/schemas)
- **Language**: TypeScript
- **Contents**: 22 domain type modules + barrel `index.ts` export
- **Types**: ActivityFeedEntry, Agent, Approval, Artifact, AuditEvent, Connector, CostRecord,
  CouncilSession, EscalationRule, ExecutionEvent, GovernancePolicy, ProjectKnowledge,
  Notification, Project, ProjectMember, ReplaySnapshot, Run, Task, TrustScore,
  CredentialVault, Workspace, and all their associated list/enum types
- **Source**: Mirrors `apps/web/types/` — canonical shared type definitions

### 2. `forgemind-utils` (packages/utils)
- **Language**: Python
- **Contents**: 4 modules — `metrics`, `rate_limit`, `error_handlers`, `logging_middleware`
- **Extracted from**: `apps/api/app/core/`
- **Key exports**: `inc_counter`, `observe_histogram`, `render_prometheus`,
  `RateLimitMiddleware`, `register_error_handlers`, `RequestLoggingMiddleware`

### 3. `forgemind-security` (packages/security)
- **Language**: Python
- **Contents**: 2 modules — `jwt`, `rbac`
- **jwt**: Stateless `create_token`/`decode_token` with `JWTConfig` dataclass
- **rbac**: `Action` enum (20 actions), `WorkspaceRole`/`ProjectRole` enums,
  permission matrices, pure `is_workspace_action_allowed`/`is_project_action_allowed` checks
- **Design**: DB-independent so it can be used across services or in tests

### 4. `forgemind-core` (packages/core)
- **Language**: Python
- **Contents**: 2 modules — `constants`, `llm`
- **constants**: Frozen sets for all domain statuses (`PROJECT_STATUSES`, `RUN_STATUSES`,
  `TASK_STATUSES`, `ARTIFACT_TYPES`, `AGENT_STATUSES`)
- **llm**: Thin async LiteLLM wrapper with `LLMConfig` dataclass

## Tests

10 new tests in `test_fm079_packages.py`:
- Schema package: source file count, barrel export validation, package.json metadata
- Utils package: file structure, metrics round-trip
- Security package: file structure, RBAC engine correctness, JWT round-trip
- Core package: file structure, domain constants validation

## Test Results

- **369/369 tests passing** (359 existing + 10 new)
- No regressions in existing tests
- Pre-existing TS errors in sidebar.tsx (unrelated)

## Files Created

- `packages/schemas/src/` — 23 TypeScript files (22 domain + index.ts)
- `packages/utils/pyproject.toml` + `forgemind_utils/` (4 modules + __init__.py)
- `packages/security/pyproject.toml` + `forgemind_security/` (2 modules + __init__.py)
- `packages/core/pyproject.toml` + `forgemind_core/` (2 modules + __init__.py)
- `apps/api/tests/test_fm079_packages.py` — 10 tests
- Updated READMEs for all 4 packages
