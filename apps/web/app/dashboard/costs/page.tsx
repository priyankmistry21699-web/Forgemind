"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { fetchCostRecords, fetchCostBreakdown } from "@/lib/costs";
import type { CostRecord, CostSummary } from "@/types/cost";

export default function CostsPage() {
  const [records, setRecords] = useState<CostRecord[]>([]);
  const [total, setTotal] = useState(0);
  const [breakdown, setBreakdown] = useState<CostSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [data, bd] = await Promise.all([fetchCostRecords(), fetchCostBreakdown()]);
      setRecords(data.items);
      setTotal(data.total);
      setBreakdown(bd);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load cost data");
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
        <span className="text-[var(--color-text)]">Costs</span>
      </div>

      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Cost Tracking</h1>
        <p className="mt-1 text-sm text-[var(--color-text-muted)]">
          LLM usage costs and token consumption ({total} records)
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

      {/* Breakdown summary */}
      {!loading && breakdown && (
        <div className="grid grid-cols-3 gap-4">
          <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-bg-card)] p-4">
            <p className="text-[10px] uppercase text-[var(--color-text-dim)]">Total Spend</p>
            <p className="text-xl font-semibold text-[var(--color-text)]">
              ${breakdown.total_cost_usd.toFixed(4)}
            </p>
          </div>
          <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-bg-card)] p-4">
            <p className="text-[10px] uppercase text-[var(--color-text-dim)]">Total Tokens</p>
            <p className="text-xl font-semibold text-[var(--color-text)]">
              {breakdown.total_tokens.toLocaleString()}
            </p>
          </div>
          <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-bg-card)] p-4">
            <p className="text-[10px] uppercase text-[var(--color-text-dim)]">Records</p>
            <p className="text-xl font-semibold text-[var(--color-text)]">
              {breakdown.record_count}
            </p>
          </div>
        </div>
      )}

      {/* Model breakdown */}
      {!loading && breakdown && Object.keys(breakdown.by_model).length > 0 && (
        <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-bg-card)] p-4">
          <p className="text-xs font-medium uppercase text-[var(--color-text-dim)] mb-3">By Model</p>
          <div className="space-y-2">
            {Object.entries(breakdown.by_model).map(([model, stats]) => (
              <div key={model} className="flex items-center justify-between text-sm">
                <span className="font-medium text-[var(--color-text)]">{model}</span>
                <div className="flex gap-4 text-[var(--color-text-muted)]">
                  <span>${stats.cost_usd.toFixed(4)}</span>
                  <span>{stats.tokens.toLocaleString()} tokens</span>
                  <span>{stats.count} calls</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Empty state */}
      {!loading && records.length === 0 && (
        <div className="rounded-xl border border-dashed border-[var(--color-border)] p-12 text-center">
          <p className="text-sm text-[var(--color-text-muted)]">No cost records yet.</p>
        </div>
      )}

      {/* Record list */}
      {!loading && records.length > 0 && (
        <div className="space-y-3">
          {records.map((rec) => (
            <div
              key={rec.id}
              className="rounded-xl border border-[var(--color-border)] bg-[var(--color-bg-card)] p-4"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-semibold text-[var(--color-text)]">
                    {rec.model_name}
                  </span>
                  <span className="rounded bg-[var(--color-bg-secondary)] px-1.5 py-0.5 text-[10px] text-[var(--color-text-muted)]">
                    {rec.caller}
                  </span>
                </div>
                <span className="text-sm font-semibold text-emerald-400">
                  ${rec.cost_usd.toFixed(4)}
                </span>
              </div>
              <div className="mt-2 grid grid-cols-4 gap-4">
                <div>
                  <p className="text-[10px] uppercase text-[var(--color-text-dim)]">Prompt</p>
                  <p className="text-sm text-[var(--color-text)]">{rec.prompt_tokens.toLocaleString()}</p>
                </div>
                <div>
                  <p className="text-[10px] uppercase text-[var(--color-text-dim)]">Completion</p>
                  <p className="text-sm text-[var(--color-text)]">{rec.completion_tokens.toLocaleString()}</p>
                </div>
                <div>
                  <p className="text-[10px] uppercase text-[var(--color-text-dim)]">Total</p>
                  <p className="text-sm text-[var(--color-text)]">{rec.total_tokens.toLocaleString()}</p>
                </div>
                <div>
                  <p className="text-[10px] uppercase text-[var(--color-text-dim)]">Time</p>
                  <p className="text-sm text-[var(--color-text-muted)]">
                    {new Date(rec.created_at).toLocaleString()}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
