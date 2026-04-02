"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { fetchTrustScores } from "@/lib/trust";
import type { TrustScore } from "@/types/trust";

const RISK_COLORS: Record<string, string> = {
  low: "bg-emerald-500/10 text-emerald-400",
  medium: "bg-yellow-500/10 text-yellow-400",
  high: "bg-orange-500/10 text-orange-400",
  critical: "bg-red-500/10 text-red-400",
};

const ENTITY_ICONS: Record<string, string> = {
  task: "☐",
  artifact: "📦",
  run: "▶",
};

export default function TrustPage() {
  const [scores, setScores] = useState<TrustScore[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchTrustScores();
      setScores(data.items);
      setTotal(data.total);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load trust scores");
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
        <span className="text-[var(--color-text)]">Trust</span>
      </div>

      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Trust Scores</h1>
        <p className="mt-1 text-sm text-[var(--color-text-muted)]">
          Risk assessment and trust scoring across platform entities ({total} assessments)
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
      {!loading && scores.length === 0 && (
        <div className="rounded-xl border border-dashed border-[var(--color-border)] p-12 text-center">
          <p className="text-sm text-[var(--color-text-muted)]">No trust assessments recorded yet.</p>
        </div>
      )}

      {/* Score list */}
      {!loading && scores.length > 0 && (
        <div className="space-y-3">
          {scores.map((score) => (
            <div
              key={score.id}
              className="rounded-xl border border-[var(--color-border)] bg-[var(--color-bg-card)] p-4"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-sm">{ENTITY_ICONS[score.entity_type] ?? "•"}</span>
                  <span className="rounded bg-[var(--color-bg-secondary)] px-1.5 py-0.5 text-[10px] font-medium uppercase">
                    {score.entity_type}
                  </span>
                  <span className="text-sm font-semibold text-[var(--color-text)]">
                    {score.entity_id.slice(0, 8)}…
                  </span>
                </div>
                <span
                  className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${
                    RISK_COLORS[score.risk_level] ?? "bg-[var(--color-bg-secondary)] text-[var(--color-text-dim)]"
                  }`}
                >
                  {score.risk_level}
                </span>
              </div>

              <div className="mt-3 grid grid-cols-3 gap-4">
                <div>
                  <p className="text-[10px] uppercase text-[var(--color-text-dim)]">Trust Score</p>
                  <p className="text-lg font-semibold text-[var(--color-text)]">
                    {(score.trust_score * 100).toFixed(0)}%
                  </p>
                </div>
                <div>
                  <p className="text-[10px] uppercase text-[var(--color-text-dim)]">Confidence</p>
                  <p className="text-lg font-semibold text-[var(--color-text)]">
                    {(score.confidence * 100).toFixed(0)}%
                  </p>
                </div>
                <div>
                  <p className="text-[10px] uppercase text-[var(--color-text-dim)]">Assessed</p>
                  <p className="text-sm text-[var(--color-text-muted)]">
                    {new Date(score.assessed_at).toLocaleString()}
                  </p>
                </div>
              </div>

              {score.factors && Object.keys(score.factors).length > 0 && (
                <div className="mt-3 border-t border-[var(--color-border)] pt-3">
                  <p className="text-[10px] uppercase text-[var(--color-text-dim)] mb-1">Factors</p>
                  <div className="flex flex-wrap gap-1.5">
                    {Object.entries(score.factors).map(([key, val]) => (
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
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
