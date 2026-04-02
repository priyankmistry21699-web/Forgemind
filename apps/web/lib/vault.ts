import { apiFetch } from "@/lib/api";
import type { CredentialVaultList, CredentialVault } from "@/types/vault";

/** Fetch paginated vault credentials. */
export async function fetchCredentials(
  offset = 0,
  limit = 50,
): Promise<CredentialVaultList> {
  return apiFetch<CredentialVaultList>(
    `/vault/credentials?offset=${offset}&limit=${limit}`,
  );
}

/** Fetch a single credential by ID. */
export async function fetchCredential(id: string): Promise<CredentialVault> {
  return apiFetch<CredentialVault>(`/vault/credentials/${id}`);
}
