"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { fetchConnectors } from "@/lib/connectors";
import type { Connector, ConnectorStatus } from "@/types/connector";

const STATUS_COLORS: Record<ConnectorStatus, string> = {
  available: "bg-blue-500/10 text-blue-400",
  configured: "bg-emerald-500/10 text-emerald-400",
  unavailable: "bg-red-500/10 text-red-400",
};

export default function ConnectorsPage() {
  const [connectors, setConnectors] = useState<Connector[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchConnectors();
      setConnectors(data.items);
      setTotal(data.total);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load connectors");
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
        <span className="text-[var(--color-text)]">Connectors</span>
      </div>

      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Connectors</h1>
        <p className="mt-1 text-sm text-[var(--color-text-muted)]">
          External tool and service integrations ({total} registered)
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
      {!loading && connectors.length === 0 && (
        <div className="rounded-xl border border-dashed border-[var(--color-border)] p-12 text-center">
          <p className="text-sm text-[var(--color-text-muted)]">No connectors registered yet.</p>
        </div>
      )}

      {/* Connector list */}
      {!loading && connectors.length > 0 && (
        <div className="space-y-3">
          {connectors.map((conn) => (
            <div
              key={conn.id}
              className="rounded-xl border border-[var(--color-border)] bg-[var(--color-bg-card)] p-4"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-semibold text-[var(--color-text)]">
                    {conn.name}
                  </span>
                  <span className="rounded bg-[var(--color-bg-secondary)] px-1.5 py-0.5 text-[10px] font-medium uppercase text-[var(--color-text-muted)]">
                    {conn.connector_type}
                  </span>
                </div>
                <span
                  className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${STATUS_COLORS[conn.status]}`}
                >
                  {conn.status}
                </span>
              </div>

              {conn.description && (
                <p className="mt-1 text-xs text-[var(--color-text-muted)]">{conn.description}</p>
              )}

              <div className="mt-3 grid grid-cols-3 gap-4">
                <div>
                  <p className="text-[10px] uppercase text-[var(--color-text-dim)]">Slug</p>
                  <p className="font-mono text-xs text-[var(--color-text)]">{conn.slug}</p>
                </div>
                <div>
                  <p className="text-[10px] uppercase text-[var(--color-text-dim)]">Capabilities</p>
                  <p className="text-xs text-[var(--color-text)]">
                    {conn.capabilities?.length ?? 0}
                  </p>
                </div>
                <div>
                  <p className="text-[10px] uppercase text-[var(--color-text-dim)]">Created</p>
                  <p className="text-xs text-[var(--color-text-muted)]">
                    {new Date(conn.created_at).toLocaleDateString()}
                  </p>
                </div>
              </div>

              {conn.capabilities && conn.capabilities.length > 0 && (
                <div className="mt-2 border-t border-[var(--color-border)] pt-2">
                  <div className="flex flex-wrap gap-1.5">
                    {conn.capabilities.map((cap) => (
                      <span
                        key={cap}
                        className="rounded bg-[var(--color-bg-secondary)] px-1.5 py-0.5 text-[10px] text-[var(--color-text-muted)]"
                      >
                        {cap}
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
