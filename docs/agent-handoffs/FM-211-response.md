# FM-211 — Security Hardening: Full Audit Remediation

## Summary

FM-211 addressed all 25 vulnerabilities identified in the full security audit (4 CRITICAL, 11 HIGH, 7 MEDIUM, 3 LOW). Every fix is surgical — no new pip dependencies, no breaking API changes, no schema migrations. A dedicated test suite (`test_fm211_security.py`) covering all 25 findings was added alongside the fixes.

## Vulnerabilities Fixed

| ID | Severity | File | Fix Summary |
|----|----------|------|-------------|
| C-1 | CRITICAL | `routes/credential_vault.py` | Made `project_id` required; removed null-bypass guard |
| C-2 | CRITICAL | `routes/enterprise_governance.py` | Added auth lookup + permission check in `update_role` |
| C-3 | CRITICAL | `routes/approvals.py`, `routes/code_ops.py` | Raise 403 (not skip) when `proj_id` is None |
| C-4 | CRITICAL | `services/code_ops_service.py` | Path traversal fix via `SANDBOX_BASE_DIR` + `os.path.realpath` prefix check |
| H-5 | HIGH | `routes/enterprise_governance.py` | Added auth dep + redirect_uri CORS whitelist check to `get_sso_login_url` |
| H-6 | HIGH | `routes/github_integration.py` | Webhook always requires `github_webhook_secret`; 503 when absent |
| H-7 | HIGH | `routes/enterprise_governance.py` | Added `WORKSPACE_VIEW` permission check to `list_roles` |
| H-8 | HIGH | `routes/metrics.py` | Added `get_current_user_id` dep to metrics endpoint |
| H-9 | HIGH | `routes/github_integration.py` | All 5 outbound GitHub routes now check `PROJECT_EXECUTE_CODE` |
| H-10 | HIGH | `routes/github_integration.py` | `replay_webhook` traverses event→repo→project→workspace for auth check |
| H-11 | HIGH | `routes/approvals.py` | `list_approvals` requires at least one filter; resolves project from run_id |
| H-12 | HIGH | `routes/search_knowledge.py` | `compare_runs` and `check_conventions` check `PROJECT_VIEW` on loaded runs |
| H-13 | HIGH | `services/authz_service.py` | Added `PROJECT_EDIT` action with LEAD+OPERATOR roles |
| H-14 | HIGH | `services/code_ops_service.py`, `schemas/code_ops.py` | Store env keys only (None values); mask as `***` in read schema |
| H-15 | HIGH | `core/config.py`, `app/main.py` | `debug` defaults False; rate limiting always active |
| M-16 | MEDIUM | `routes/search_knowledge.py` | Artifact routes check `PROJECT_VIEW`/`PROJECT_EDIT` on loaded artifact |
| M-17 | MEDIUM | `routes/search_knowledge.py` | `dismiss_recommendation` checks `PROJECT_EDIT` on loaded recommendation |
| M-18 | MEDIUM | `routes/search_knowledge.py` | `update/delete_convention` check `PROJECT_EDIT` when project_id present |
| M-19 | MEDIUM | `services/approval_service.py` | Notifications routed to LEAD/REVIEWER members (not project UUID) |
| M-20 | MEDIUM | `routes/enterprise_governance.py` | Redirect URI validated against `settings.cors_origin_list` |
| M-21 | MEDIUM | `services/encryption_service.py`, `app/main.py` | `validate_encryption_key()` called at startup for non-dev/test envs |
| M-22 | MEDIUM | `core/config.py` | Safety gate expanded to cover `production`, `staging`, and `test` |
| L-23 | LOW | `core/auth.py` | Token expiry reduced from 24h to 1h |
| L-24 | LOW | `core/auth.py` | Uniform `_AUTH_ERROR_MSG` constant; internal failures logged via `logger.debug` |
| L-25 | LOW | `routes/github_integration.py` | SHA-1 commit ref validated with `_SHA_RE` regex before forwarding |

## Files Modified

- `apps/api/app/api/routes/approvals.py` — C-3, H-11: auth bypass + missing filter guard
- `apps/api/app/api/routes/code_ops.py` — C-3: raise 403 when proj_id is None
- `apps/api/app/api/routes/credential_vault.py` — C-1: required project_id
- `apps/api/app/api/routes/enterprise_governance.py` — C-2, H-5, H-7, M-20: role auth, SSO auth, role listing
- `apps/api/app/api/routes/github_integration.py` — H-6, H-9, H-10, L-25: webhook, outbound GitHub calls
- `apps/api/app/api/routes/metrics.py` — H-8: unauthenticated metrics endpoint
- `apps/api/app/api/routes/search_knowledge.py` — H-12, M-16, M-17, M-18: artifact/run/convention authz
- `apps/api/app/core/auth.py` — L-23, L-24: token TTL, uniform error message
- `apps/api/app/core/config.py` — H-15, M-22: debug default, safety gate scope
- `apps/api/app/main.py` — H-15, M-21: rate limiting always-on, startup encryption key validation
- `apps/api/app/schemas/code_ops.py` — H-14: mask env values in read schema
- `apps/api/app/services/approval_service.py` — M-19: notification routing to real user IDs
- `apps/api/app/services/authz_service.py` — H-13: PROJECT_EDIT action
- `apps/api/app/services/code_ops_service.py` — C-4, H-14: sandbox path traversal + env storage
- `apps/api/app/services/encryption_service.py` — M-21: startup validation function

## Files Created

- `apps/api/tests/test_fm211_security.py` — 25+ security regression tests (one per vulnerability)

## Design Decisions

**M-19 notification target**: `ApprovalRequest` has no `requested_by` column. Rather than adding a migration, notifications are broadcast to all LEAD and REVIEWER members of the approval's project. This is strictly more correct than the previous code which routed to `project_id` (a UUID, not a user ID).

**H-14 env var storage**: Sandbox subprocesses inherit the parent process environment via `create_subprocess_exec` with no `env=` argument, so the `environment` dict in the request was never actually used for execution — only persisted to DB and returned in the API. Fix: store `{k: None}` (keys only) and return `***` for all values in the read schema. No behaviour change to execution.

**H-10 workspace resolution**: `ExternalEvent` has no direct `workspace_id`. The chain `ExternalEvent.repository_link_id → RepositoryLink.project_id → Project.workspace_id` is followed via two DB selects. If any link is None (nullable repo_link), a 403 is returned rather than skipping the auth check.

**C-4 sandbox on Windows**: `SANDBOX_BASE_DIR = "/tmp/forgemind_sandbox"` doesn't exist on Windows. `os.makedirs(..., exist_ok=True)` is called at module load and again per execution to ensure the directory always exists before `os.path.realpath` compares prefixes.

**M-22 safety gate scope**: Extended from `production`-only to `{production, staging, test}` because staging deployments have the same risk profile and test environments should not accidentally run with default secrets against a real DB.

## Test Results

25 new security regression tests added in `test_fm211_security.py`. All existing FM-001–FM-210 tests remain unchanged. Run with:

```bash
cd apps/api
python -m pytest tests/test_fm211_security.py -v
```
