"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { fetchGovernancePolicies } from "@/lib/governance";
import type { GovernancePolicy } from "@/types/governance";

const TRIGGER_COLORS: Record<string, string> = {
  task_type: "bg-blue-500/10 text-blue-400",
  cost_threshold: "bg-orange-500/10 text-orange-400",
  artifact_type: "bg-purple-500/10 text-purple-400",
  agent_action: "bg-teal-500/10 text-teal-400",
  custom: "bg-[var(--color-bg-secondary)] text-[var(--color-text-dim)]",
};

const ACTION_COLORS: Record<string, string> = {
  require_approval: "bg-yellow-500/10 text-yellow-400",
  auto_approve: "bg-emerald-500/10 text-emerald-400",
  block: "bg-red-500/10 text-red-400",
  notify: "bg-blue-500/10 text-blue-400",
};

export default function GovernancePage() {
  const [policies, setPolicies] = useState<GovernancePolicy[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchGovernancePolicies();
      setPolicies(data.items);
      setTotal(data.total);
    } catch (err: unknown) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to load governance policies",
      );
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
        <Link
          href="/dashboard"
          className="hover:text-[var(--color-text)] transition-colors"
        >
          Dashboard
        </Link>
        <span>/</span>
        <span className="text-[var(--color-text)]">Governance</span>
      </div>

      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight">
          Governance Policies
        </h1>
        <p className="mt-1 text-sm text-[var(--color-text-muted)]">
          Policy-based approval rules and automated governance ({total}{" "}
          policies)
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
      {!loading && policies.length === 0 && (
        <div className="rounded-xl border border-dashed border-[var(--color-border)] p-12 text-center">
          <p className="text-sm text-[var(--color-text-muted)]">
            No governance policies configured yet.
          </p>
        </div>
      )}

      {/* Policy list */}
      {!loading && policies.length > 0 && (
        <div className="space-y-3">
          {policies.map((policy) => (
            <div
              key={policy.id}
              className="rounded-xl border border-[var(--color-border)] bg-[var(--color-bg-card)] p-4"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <h3 className="font-semibold text-[var(--color-text)]">
                    {policy.name}
                  </h3>
                  <span className="rounded bg-[var(--color-bg-secondary)] px-1.5 py-0.5 text-[10px] text-[var(--color-text-dim)]">
                    P{policy.priority}
                  </span>
                </div>
                <span
                  className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${
                    policy.enabled
                      ? "bg-emerald-500/10 text-emerald-400"
                      : "bg-[var(--color-bg-secondary)] text-[var(--color-text-dim)]"
                  }`}
                >
                  {policy.enabled ? "Enabled" : "Disabled"}
                </span>
              </div>

              {policy.description && (
                <p className="mt-1 text-sm text-[var(--color-text-muted)]">
                  {policy.description}
                </p>
              )}

              <div className="mt-2 flex items-center gap-2">
                <span
                  className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${
                    TRIGGER_COLORS[policy.trigger] ??
                    "bg-[var(--color-bg-secondary)] text-[var(--color-text-dim)]"
                  }`}
                >
                  trigger: {policy.trigger.replace(/_/g, " ")}
                </span>
                <span
                  className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${
                    ACTION_COLORS[policy.action] ??
                    "bg-[var(--color-bg-secondary)] text-[var(--color-text-dim)]"
                  }`}
                >
                  action: {policy.action.replace(/_/g, " ")}
                </span>
              </div>

              {policy.rules && Object.keys(policy.rules).length > 0 && (
                <div className="mt-3 border-t border-[var(--color-border)] pt-3">
                  <p className="text-[10px] uppercase text-[var(--color-text-dim)] mb-1">
                    Rules
                  </p>
                  <div className="flex flex-wrap gap-1.5">
                    {Object.entries(policy.rules).map(([key, val]) => (
                      <span
                        key={key}
                        className="rounded bg-[var(--color-bg-secondary)] px-1.5 py-0.5 text-[10px] text-[var(--color-text-muted)]"
                      >
                        {key}: {String(val)}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              <div className="mt-2 text-[10px] text-[var(--color-text-dim)]">
                Updated {new Date(policy.updated_at).toLocaleString()}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
