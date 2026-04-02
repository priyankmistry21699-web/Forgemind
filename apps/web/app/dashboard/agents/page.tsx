"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { fetchAgents } from "@/lib/agents";
import type { Agent, AgentStatus } from "@/types/agent";

const STATUS_COLORS: Record<AgentStatus, string> = {
  active: "bg-emerald-500/10 text-emerald-400",
  inactive: "bg-yellow-500/10 text-yellow-400",
  deprecated: "bg-red-500/10 text-red-400",
};

export default function AgentsPage() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchAgents();
      setAgents(data.items);
      setTotal(data.total);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load agents");
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
        <span className="text-[var(--color-text)]">Agents</span>
      </div>

      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Agents</h1>
        <p className="mt-1 text-sm text-[var(--color-text-muted)]">
          Registered AI agents and their capabilities ({total} agents)
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
      {!loading && agents.length === 0 && (
        <div className="rounded-xl border border-dashed border-[var(--color-border)] p-12 text-center">
          <p className="text-sm text-[var(--color-text-muted)]">No agents registered yet.</p>
        </div>
      )}

      {/* Agent list */}
      {!loading && agents.length > 0 && (
        <div className="space-y-3">
          {agents.map((agent) => (
            <div
              key={agent.id}
              className="rounded-xl border border-[var(--color-border)] bg-[var(--color-bg-card)] p-4"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-semibold text-[var(--color-text)]">
                    {agent.name}
                  </span>
                  <span className="font-mono text-[10px] text-[var(--color-text-dim)]">
                    {agent.slug}
                  </span>
                </div>
                <span
                  className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${STATUS_COLORS[agent.status]}`}
                >
                  {agent.status}
                </span>
              </div>

              {agent.description && (
                <p className="mt-1 text-xs text-[var(--color-text-muted)]">{agent.description}</p>
              )}

              <div className="mt-3 grid grid-cols-2 gap-4">
                <div>
                  <p className="text-[10px] uppercase text-[var(--color-text-dim)]">Capabilities</p>
                  {agent.capabilities && agent.capabilities.length > 0 ? (
                    <div className="mt-1 flex flex-wrap gap-1.5">
                      {agent.capabilities.map((cap) => (
                        <span
                          key={cap}
                          className="rounded bg-[var(--color-bg-secondary)] px-1.5 py-0.5 text-[10px] text-[var(--color-text-muted)]"
                        >
                          {cap}
                        </span>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-[var(--color-text-dim)]">—</p>
                  )}
                </div>
                <div>
                  <p className="text-[10px] uppercase text-[var(--color-text-dim)]">Task Types</p>
                  {agent.supported_task_types && agent.supported_task_types.length > 0 ? (
                    <div className="mt-1 flex flex-wrap gap-1.5">
                      {agent.supported_task_types.map((tt) => (
                        <span
                          key={tt}
                          className="rounded bg-blue-500/10 px-1.5 py-0.5 text-[10px] text-blue-400"
                        >
                          {tt}
                        </span>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-[var(--color-text-dim)]">—</p>
                  )}
                </div>
              </div>

              <div className="mt-2 text-[10px] text-[var(--color-text-dim)]">
                Created {new Date(agent.created_at).toLocaleDateString()}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
