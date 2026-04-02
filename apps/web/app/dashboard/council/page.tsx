"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { fetchCouncilSessions } from "@/lib/council";
import type { CouncilSession, CouncilVote } from "@/types/council";

const STATUS_COLORS: Record<string, string> = {
  decided: "bg-emerald-500/10 text-emerald-400",
  deliberating: "bg-blue-500/10 text-blue-400",
  convened: "bg-[var(--color-bg-secondary)] text-[var(--color-text-dim)]",
  deadlocked: "bg-red-500/10 text-red-400",
  escalated: "bg-orange-500/10 text-orange-400",
};

const VOTE_COLORS: Record<string, string> = {
  approve: "bg-emerald-500/10 text-emerald-400",
  reject: "bg-red-500/10 text-red-400",
  abstain: "bg-[var(--color-bg-secondary)] text-[var(--color-text-dim)]",
  modify: "bg-yellow-500/10 text-yellow-400",
};

export default function CouncilPage() {
  const [sessions, setSessions] = useState<CouncilSession[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchCouncilSessions();
      setSessions(data.items);
      setTotal(data.total);
    } catch (err: unknown) {
      setError(
        err instanceof Error ? err.message : "Failed to load council sessions",
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
        <span className="text-[var(--color-text)]">Council</span>
      </div>

      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Council Sessions</h1>
        <p className="mt-1 text-sm text-[var(--color-text-muted)]">
          Multi-agent decision-making history ({total} sessions)
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
      {!loading && sessions.length === 0 && (
        <div className="rounded-xl border border-dashed border-[var(--color-border)] p-12 text-center">
          <p className="text-sm text-[var(--color-text-muted)]">
            No council sessions convened yet.
          </p>
        </div>
      )}

      {/* Session list */}
      {!loading && sessions.length > 0 && (
        <div className="space-y-3">
          {sessions.map((session) => (
            <div
              key={session.id}
              className="rounded-xl border border-[var(--color-border)] bg-[var(--color-bg-card)] p-4"
            >
              <div className="flex items-center justify-between">
                <h3 className="font-semibold text-[var(--color-text)]">
                  {session.topic}
                </h3>
                <span
                  className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${
                    STATUS_COLORS[session.status] ??
                    "bg-[var(--color-bg-secondary)] text-[var(--color-text-dim)]"
                  }`}
                >
                  {session.status}
                </span>
              </div>

              {session.description && (
                <p className="mt-1 text-sm text-[var(--color-text-muted)]">
                  {session.description}
                </p>
              )}

              <div className="mt-2 flex items-center gap-3 text-[10px] text-[var(--color-text-muted)]">
                <span className="rounded bg-[var(--color-bg-secondary)] px-1.5 py-0.5">
                  {session.decision_method}
                </span>
                <span>
                  {session.votes.length} vote
                  {session.votes.length !== 1 ? "s" : ""}
                </span>
                <span>{new Date(session.convened_at).toLocaleString()}</span>
              </div>

              {session.final_decision && (
                <div className="mt-2 rounded bg-emerald-500/5 p-2 text-xs text-emerald-400">
                  Decision: {session.final_decision}
                </div>
              )}

              {session.decision_rationale && (
                <p className="mt-1 text-xs text-[var(--color-text-dim)]">
                  Rationale: {session.decision_rationale}
                </p>
              )}

              {/* Expandable votes */}
              {session.votes.length > 0 && (
                <div className="mt-3 border-t border-[var(--color-border)] pt-3">
                  <button
                    onClick={() =>
                      setExpandedId(
                        expandedId === session.id ? null : session.id,
                      )
                    }
                    className="text-[10px] font-medium uppercase tracking-wider text-[var(--color-accent)] hover:text-[var(--color-accent-hover)] transition-colors"
                  >
                    {expandedId === session.id ? "Hide votes" : "Show votes"}
                  </button>

                  {expandedId === session.id && (
                    <div className="mt-2 space-y-2">
                      {session.votes.map((vote: CouncilVote) => (
                        <div
                          key={vote.id}
                          className="flex items-center justify-between rounded-lg bg-[var(--color-bg-secondary)] p-2"
                        >
                          <div className="flex items-center gap-2">
                            <span className="text-xs font-medium text-[var(--color-text)]">
                              {vote.agent_slug}
                            </span>
                            <span
                              className={`rounded-full px-1.5 py-0.5 text-[9px] font-medium ${
                                VOTE_COLORS[vote.decision] ??
                                "bg-[var(--color-bg-secondary)] text-[var(--color-text-dim)]"
                              }`}
                            >
                              {vote.decision}
                            </span>
                          </div>
                          <div className="flex items-center gap-2 text-[10px] text-[var(--color-text-dim)]">
                            <span>
                              conf: {(vote.confidence * 100).toFixed(0)}%
                            </span>
                            <span>wt: {vote.weight.toFixed(1)}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
