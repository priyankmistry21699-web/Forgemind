"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { fetchCredentials } from "@/lib/vault";
import type { CredentialVault, SecretStatus } from "@/types/vault";

const STATUS_COLORS: Record<SecretStatus, string> = {
  active: "bg-emerald-500/10 text-emerald-400",
  expired: "bg-yellow-500/10 text-yellow-400",
  missing: "bg-red-500/10 text-red-400",
  revoked: "bg-gray-500/10 text-gray-400",
};

export default function VaultPage() {
  const [credentials, setCredentials] = useState<CredentialVault[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchCredentials();
      setCredentials(data.items);
      setTotal(data.total);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load credentials");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div className="space-y-6">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-xs text-[var(--color-text-muted)]">
        <Link href="/dashboard" className="hover:text-[var(--color-text)] transition-colors">
          Dashboard
        </Link>
        <span>/</span>
        <span className="text-[var(--color-text)]">Vault</span>
      </div>

      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Credential Vault</h1>
        <p className="mt-1 text-sm text-[var(--color-text-muted)]">
          Securely managed secrets and API credentials ({total} stored)
        </p>
      </div>

      {/* Error */}
      {error && (
        <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-400">
          {error}
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="flex items-center justify-center py-12">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-[var(--color-accent)] border-t-transparent" />
        </div>
      )}

      {/* Empty state */}
      {!loading && credentials.length === 0 && (
        <div className="rounded-xl border border-dashed border-[var(--color-border)] p-12 text-center">
          <p className="text-sm text-[var(--color-text-muted)]">No credentials stored yet.</p>
        </div>
      )}

      {/* Credential list */}
      {!loading && credentials.length > 0 && (
        <div className="space-y-3">
          {credentials.map((cred) => (
            <div
              key={cred.id}
              className="rounded-xl border border-[var(--color-border)] bg-[var(--color-bg-card)] p-4"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-semibold text-[var(--color-text)]">
                    {cred.name}
                  </span>
                  <span
                    className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${STATUS_COLORS[cred.status]}`}
                  >
                    {cred.status}
                  </span>
                  <span className="rounded bg-[var(--color-bg-secondary)] px-1.5 py-0.5 text-[10px] text-[var(--color-text-muted)]">
                    {cred.secret_type}
                  </span>
                </div>
                <span className="font-mono text-xs text-[var(--color-text-dim)]">
                  {cred.masked_preview}
                </span>
              </div>

              {cred.description && (
                <p className="mt-1 text-xs text-[var(--color-text-muted)]">{cred.description}</p>
              )}

              <div className="mt-3 grid grid-cols-4 gap-4">
                <div>
                  <p className="text-[10px] uppercase text-[var(--color-text-dim)]">Env Key</p>
                  <p className="font-mono text-xs text-[var(--color-text)]">{cred.env_key}</p>
                </div>
                <div>
                  <p className="text-[10px] uppercase text-[var(--color-text-dim)]">Connector</p>
                  <p className="text-xs text-[var(--color-text)]">
                    {cred.connector_slug ?? "—"}
                  </p>
                </div>
                <div>
                  <p className="text-[10px] uppercase text-[var(--color-text-dim)]">Set</p>
                  <p className="text-xs text-[var(--color-text)]">
                    {cred.is_set ? "✓ Yes" : "✗ No"}
                  </p>
                </div>
                <div>
                  <p className="text-[10px] uppercase text-[var(--color-text-dim)]">Expires</p>
                  <p className="text-xs text-[var(--color-text-muted)]">
                    {cred.expires_at ? new Date(cred.expires_at).toLocaleDateString() : "Never"}
                  </p>
                </div>
              </div>

              {cred.scopes && cred.scopes.length > 0 && (
                <div className="mt-2 border-t border-[var(--color-border)] pt-2">
                  <p className="text-[10px] uppercase text-[var(--color-text-dim)] mb-1">Scopes</p>
                  <div className="flex flex-wrap gap-1.5">
                    {cred.scopes.map((scope) => (
                      <span
                        key={scope}
                        className="rounded bg-[var(--color-bg-secondary)] px-1.5 py-0.5 text-[10px] text-[var(--color-text-muted)]"
                      >
                        {scope}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
