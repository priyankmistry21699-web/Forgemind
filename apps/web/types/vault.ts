/** Credential vault types matching the backend schemas (FM-042). */

export type SecretStatus = "active" | "expired" | "missing" | "revoked";

export interface CredentialVault {
  id: string;
  name: string;
  description: string | null;
  env_key: string;
  connector_id: string | null;
  connector_slug: string | null;
  project_id: string | null;
  status: SecretStatus;
  secret_type: string;
  scopes: string[] | null;
  expires_at: string | null;
  last_rotated_at: string | null;
  is_set: boolean;
  masked_preview: string;
  created_at: string;
  updated_at: string;
}

export interface CredentialVaultList {
  items: CredentialVault[];
  total: number;
}
