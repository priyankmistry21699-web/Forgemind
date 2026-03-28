"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { fetchActivity } from "@/lib/activity";
import type { ActivityFeedEntry } from "@/types/activity";

const TYPE_ICONS: Record<string, string> = {
  run_started: "\u25B6",
  run_completed: "\u2714",
  run_failed: "\u2718",
  task_completed: "\u2713",
  approval_requested: "\u2709",
  approval_decided: "\u2696",
  member_added: "\u002B",
  member_removed: "\u2212",
  escalation_triggered: "\u26A0",
  project_created: "\u2605",
  artifact_created: "\u{1F4E6}",
};

export default function ActivityPage() {
  const [entries, setEntries] = useState<ActivityFeedEntry[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchActivity();
      setEntries(data.items);
      setTotal(data.total);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load activity");
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
        <span className="text-[var(--color-text)]">Activity</span>
      </div>

      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Activity Feed</h1>
        <p className="mt-1 text-sm text-[var(--color-text-muted)]">
          Real-time view of all operations across the platform ({total} events)
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

      {/* Activity list */}
      {!loading && entries.length === 0 && (
        <div className="rounded-xl border border-dashed border-[var(--color-border)] p-12 text-center">
          <p className="text-sm text-[var(--color-text-muted)]">No activity recorded yet.</p>
        </div>
      )}

      {!loading && entries.length > 0 && (
        <div className="relative space-y-0">
          {/* Timeline line */}
          <div className="absolute left-5 top-0 bottom-0 w-px bg-[var(--color-border)]" />

          {entries.map((entry) => (
            <div key={entry.id} className="relative flex gap-4 py-3 pl-3">
              {/* Timeline dot */}
              <div className="relative z-10 flex h-5 w-5 shrink-0 items-center justify-center rounded-full border border-[var(--color-border)] bg-[var(--color-bg-card)] text-[10px]">
                {TYPE_ICONS[entry.activity_type] ?? "\u2022"}
              </div>

              <div className="min-w-0 flex-1">
                <p className="text-sm text-[var(--color-text)]">{entry.summary}</p>
                <div className="mt-1 flex items-center gap-3 text-[10px] text-[var(--color-text-dim)]">
                  <span className="rounded bg-[var(--color-bg-secondary)] px-1.5 py-0.5">
                    {entry.activity_type.replace(/_/g, " ")}
                  </span>
                  <span>{new Date(entry.created_at).toLocaleString()}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
