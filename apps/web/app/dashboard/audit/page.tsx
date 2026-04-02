"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { fetchAuditSummary, exportAuditJson } from "@/lib/audit";
import type { AuditSummary, AuditEvent, EventType } from "@/types/audit";

const EVENT_COLORS: Partial<Record<EventType, string>> = {
  task_completed: "bg-emerald-500/10 text-emerald-400",
  task_claimed: "bg-blue-500/10 text-blue-400",
  task_failed: "bg-red-500/10 text-red-400",
  run_started: "bg-cyan-500/10 text-cyan-400",
  run_completed: "bg-emerald-500/10 text-emerald-400",
  run_failed: "bg-red-500/10 text-red-400",
  approval_requested: "bg-yellow-500/10 text-yellow-400",
  approval_resolved: "bg-purple-500/10 text-purple-400",
};

export default function AuditPage() {
  const [summary, setSummary] = useState<AuditSummary | null>(null);
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [summaryData, exportData] = await Promise.all([
        fetchAuditSummary(),
        exportAuditJson(),
      ]);
      setSummary(summaryData);
      setEvents(exportData.events ?? []);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load audit data");
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
        <span className="text-[var(--color-text)]">Audit</span>
      </div>

      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Audit Log</h1>
        <p className="mt-1 text-sm text-[var(--color-text-muted)]">
          Platform-wide execution events and audit trail
          {summary ? ` (${summary.total_events} events)` : ""}
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

      {/* Summary breakdown */}
      {!loading && summary && Object.keys(summary.event_breakdown).length > 0 && (
        <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-bg-card)] p-4">
          <p className="text-xs font-medium uppercase text-[var(--color-text-dim)] mb-3">Event Breakdown</p>
          <div className="flex flex-wrap gap-2">
            {Object.entries(summary.event_breakdown).map(([evtType, count]) => (
              <span
                key={evtType}
                className={`rounded-full px-2.5 py-1 text-xs font-medium ${
                  EVENT_COLORS[evtType as EventType] ?? "bg-[var(--color-bg-secondary)] text-[var(--color-text-muted)]"
                }`}
              >
                {evtType.replace(/_/g, " ")} ({count})
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Empty state */}
      {!loading && events.length === 0 && (
        <div className="rounded-xl border border-dashed border-[var(--color-border)] p-12 text-center">
          <p className="text-sm text-[var(--color-text-muted)]">No audit events recorded yet.</p>
        </div>
      )}

      {/* Event list */}
      {!loading && events.length > 0 && (
        <div className="space-y-3">
          {events.map((evt) => (
            <div
              key={evt.id}
              className="rounded-xl border border-[var(--color-border)] bg-[var(--color-bg-card)] p-4"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span
                    className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${
                      EVENT_COLORS[evt.event_type] ?? "bg-[var(--color-bg-secondary)] text-[var(--color-text-muted)]"
                    }`}
                  >
                    {evt.event_type.replace(/_/g, " ")}
                  </span>
                  <span className="text-xs text-[var(--color-text-muted)]">
                    {evt.id.slice(0, 8)}…
                  </span>
                </div>
                <span className="text-xs text-[var(--color-text-muted)]">
                  {new Date(evt.created_at).toLocaleString()}
                </span>
              </div>
              <div className="mt-2 grid grid-cols-3 gap-4">
                {evt.run_id && (
                  <div>
                    <p className="text-[10px] uppercase text-[var(--color-text-dim)]">Run</p>
                    <p className="text-xs text-[var(--color-text)]">{evt.run_id.slice(0, 8)}…</p>
                  </div>
                )}
                {evt.task_id && (
                  <div>
                    <p className="text-[10px] uppercase text-[var(--color-text-dim)]">Task</p>
                    <p className="text-xs text-[var(--color-text)]">{evt.task_id.slice(0, 8)}…</p>
                  </div>
                )}
                {evt.project_id && (
                  <div>
                    <p className="text-[10px] uppercase text-[var(--color-text-dim)]">Project</p>
                    <p className="text-xs text-[var(--color-text)]">{evt.project_id.slice(0, 8)}…</p>
                  </div>
                )}
              </div>
              {evt.payload && Object.keys(evt.payload).length > 0 && (
                <div className="mt-2 border-t border-[var(--color-border)] pt-2">
                  <p className="text-[10px] uppercase text-[var(--color-text-dim)] mb-1">Payload</p>
                  <pre className="text-[10px] text-[var(--color-text-muted)] overflow-x-auto">
                    {JSON.stringify(evt.payload, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
