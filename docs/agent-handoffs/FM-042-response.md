# FM-042 — Credential Vault Abstraction

## What was done

Created a security-first credential management system that stores only environment variable key names in the database — raw secrets are never persisted. The vault provides masked previews and status tracking for connector credentials.

## Files created

- `apps/api/app/models/credential_vault.py` — `CredentialVault` model:
  - `SecretStatus` enum: `ACTIVE`, `EXPIRED`, `MISSING`, `REVOKED`
  - Table `credential_vault` with unique `env_key` column
  - FKs to `connectors` (SET NULL) and `projects` (CASCADE)
  - `secret_type`, `scopes` (JSON), `expires_at`, `last_rotated_at`, `metadata_` (JSON)
- `apps/api/app/services/credential_vault_service.py` — Vault service:
  - `_mask_secret(env_key)`: Returns masked preview (e.g., `sk-****abc1`), never the full value
  - `_is_secret_set(env_key)`: Checks if env var is set and non-empty
  - `create_credential()`: Registers credential, resolves connector by slug, auto-detects status
  - `get_credential()`, `list_credentials()`: CRUD with project/connector filters
  - `build_credential_read()`: Assembles response with `is_set` and `masked_preview`
- `apps/api/app/api/routes/credential_vault.py` — Routes: `POST /vault/credentials`, `GET /vault/credentials`
- `apps/api/app/schemas/credential_vault.py` — Schemas:
  - `CredentialVaultRead` includes `is_set: bool` and `masked_preview: str`
  - `CredentialCheckResult` for quick status checks
- `apps/api/alembic/versions/2026_03_28_0009_0010_add_credential_vault.py` — Migration creating `credential_vault` table

## Files modified

- `apps/api/app/db/base.py` — Added `CredentialVault` import
- `apps/api/app/api/router.py` — Registered `vault_router` with tag `"vault"`

## Design decisions

- **Security-first**: Raw secrets are never stored in the database — only the env var key name. Resolution happens from `os.environ` at runtime
- Masking shows first 3 + last 4 characters only
- Connector linkage via slug-based lookup (not raw ID from client)
- `project_id=None` means the credential is global and available to all projects
