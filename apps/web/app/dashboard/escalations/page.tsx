"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { fetchEscalationRules } from "@/lib/escalations";
import type { EscalationRule } from "@/types/escalation";

export default function EscalationsPage() {
  const [rules, setRules] = useState<EscalationRule[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [projectId, setProjectId] = useState<string>("");

  const load = useCallback(async () => {
    if (!projectId) {
      setRules([]);
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await fetchEscalationRules(projectId);
      setRules(data.items);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load escalation rules");
    } finally {
      setLoading(false);
    }
  }, [projectId]);

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
        <span className="text-[var(--color-text)]">Escalations</span>
      </div>

      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Escalation Rules</h1>
        <p className="mt-1 text-sm text-[var(--color-text-muted)]">
          Configure automatic escalation triggers and actions for your projects
        </p>
      </div>

      {/* Project selector */}
      <div>
        <label className="block text-xs font-medium text-[var(--color-text-muted)] mb-1">
          Project ID
        </label>
        <input
          type="text"
          placeholder="Enter project ID to view rules"
          value={projectId}
          onChange={(e) => setProjectId(e.target.value)}
          className="w-full max-w-md rounded-lg border border-[var(--color-border)] bg-[var(--color-bg-secondary)] px-3 py-2 text-sm text-[var(--color-text)] placeholder:text-[var(--color-text-dim)]"
        />
      </div>

      {/* Error */}
      {error && (
        <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-400">
          {error}
        </div>
      )}

      {/* Loading */}
      {loading && projectId && (
        <div className="flex items-center justify-center py-12">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-[var(--color-accent)] border-t-transparent" />
        </div>
      )}

      {/* Rules list */}
      {!loading && projectId && rules.length === 0 && (
        <div className="rounded-xl border border-dashed border-[var(--color-border)] p-12 text-center">
          <p className="text-sm text-[var(--color-text-muted)]">No escalation rules for this project.</p>
        </div>
      )}

      {!loading && rules.length > 0 && (
        <div className="space-y-3">
          {rules.map((rule) => (
            <div
              key={rule.id}
              className="rounded-xl border border-[var(--color-border)] bg-[var(--color-bg-card)] p-4"
            >
              <div className="flex items-center justify-between">
                <h3 className="font-semibold text-[var(--color-text)]">{rule.name}</h3>
                <span
                  className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${
                    rule.is_active
                      ? "bg-emerald-500/10 text-emerald-400"
                      : "bg-[var(--color-bg-secondary)] text-[var(--color-text-dim)]"
                  }`}
                >
                  {rule.is_active ? "Active" : "Inactive"}
                </span>
              </div>
              <div className="mt-2 flex items-center gap-3 text-xs text-[var(--color-text-muted)]">
                <span>Trigger: {rule.trigger.replace(/_/g, " ")}</span>
                <span>Action: {rule.action.replace(/_/g, " ")}</span>
                <span>Cooldown: {rule.cooldown_minutes}m</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
