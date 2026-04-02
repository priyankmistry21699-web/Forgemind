"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { fetchExecutionTrace } from "@/lib/replay";
import type { ExecutionTrace, ReplaySnapshot } from "@/types/replay";

export default function ReplayPage() {
  const [trace, setTrace] = useState<ExecutionTrace | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [runId, setRunId] = useState<string>("");

  const load = useCallback(async () => {
    if (!runId) {
      setTrace(null);
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await fetchExecutionTrace(runId);
      setTrace(data);
    } catch (err: unknown) {
      setError(
        err instanceof Error ? err.message : "Failed to load execution trace",
      );
    } finally {
      setLoading(false);
    }
  }, [runId]);

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
        <span className="text-[var(--color-text)]">Replay</span>
      </div>

      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Execution Replay</h1>
        <p className="mt-1 text-sm text-[var(--color-text-muted)]">
          Step-by-step trace inspection and deterministic replay of agent
          executions
        </p>
      </div>

      {/* Run ID input */}
      <div>
        <label className="block text-xs font-medium text-[var(--color-text-muted)] mb-1">
          Run ID
        </label>
        <input
          type="text"
          placeholder="Enter run ID to view execution trace"
          value={runId}
          onChange={(e) => setRunId(e.target.value)}
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
      {loading && runId && (
        <div className="flex items-center justify-center py-12">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-[var(--color-accent)] border-t-transparent" />
        </div>
      )}

      {/* Empty state — no run ID */}
      {!loading && !runId && (
        <div className="rounded-xl border border-dashed border-[var(--color-border)] p-12 text-center">
          <p className="text-sm text-[var(--color-text-muted)]">
            Enter a run ID to view execution trace.
          </p>
        </div>
      )}

      {/* Empty state — run ID but no snapshots */}
      {!loading && runId && trace && trace.snapshots.length === 0 && (
        <div className="rounded-xl border border-dashed border-[var(--color-border)] p-12 text-center">
          <p className="text-sm text-[var(--color-text-muted)]">
            No replay snapshots found for this run.
          </p>
        </div>
      )}

      {/* Trace summary + snapshots */}
      {!loading && trace && trace.snapshots.length > 0 && (
        <>
          {/* Summary bar */}
          <div className="grid grid-cols-4 gap-4">
            {[
              { label: "Steps", value: trace.total_steps },
              {
                label: "Total Tokens",
                value: trace.total_tokens.toLocaleString(),
              },
              {
                label: "Total Cost",
                value: `$${trace.total_cost_usd.toFixed(4)}`,
              },
              {
                label: "Total Duration",
                value: `${(trace.total_duration_ms / 1000).toFixed(1)}s`,
              },
            ].map((stat) => (
              <div
                key={stat.label}
                className="rounded-xl border border-[var(--color-border)] bg-[var(--color-bg-card)] p-3 text-center"
              >
                <p className="text-[10px] uppercase text-[var(--color-text-dim)]">
                  {stat.label}
                </p>
                <p className="text-lg font-semibold text-[var(--color-text)]">
                  {stat.value}
                </p>
              </div>
            ))}
          </div>

          {/* Snapshot timeline */}
          <div className="relative space-y-0">
            <div className="absolute left-5 top-0 bottom-0 w-px bg-[var(--color-border)]" />

            {trace.snapshots.map((snap: ReplaySnapshot) => (
              <div key={snap.id} className="relative flex gap-4 py-3 pl-3">
                {/* Timeline dot */}
                <div className="relative z-10 flex h-5 w-5 shrink-0 items-center justify-center rounded-full border border-[var(--color-border)] bg-[var(--color-bg-card)] text-[10px] font-bold">
                  {snap.sequence_number}
                </div>

                <div className="min-w-0 flex-1 rounded-xl border border-[var(--color-border)] bg-[var(--color-bg-card)] p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-sm text-[var(--color-text)]">
                        {snap.agent_slug}
                      </span>
                      {snap.is_replay && (
                        <span className="rounded-full bg-blue-500/10 px-2 py-0.5 text-[10px] font-medium text-blue-400">
                          replay
                        </span>
                      )}
                      {snap.error && (
                        <span className="rounded-full bg-red-500/10 px-2 py-0.5 text-[10px] font-medium text-red-400">
                          error
                        </span>
                      )}
                    </div>
                    <span className="text-[10px] text-[var(--color-text-dim)]">
                      {new Date(snap.created_at).toLocaleString()}
                    </span>
                  </div>

                  <div className="mt-2 flex items-center gap-3 text-[10px] text-[var(--color-text-muted)]">
                    {snap.model_used && <span>Model: {snap.model_used}</span>}
                    <span>{snap.tokens_used} tokens</span>
                    <span>{snap.duration_ms}ms</span>
                    <span>${snap.cost_usd.toFixed(4)}</span>
                    {snap.replay_hash && (
                      <span className="font-mono">
                        {snap.replay_hash.slice(0, 12)}…
                      </span>
                    )}
                  </div>

                  {snap.error && (
                    <div className="mt-2 rounded bg-red-500/5 p-2 text-xs text-red-400">
                      {snap.error}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
