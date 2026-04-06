"use client";

import { useCallback, useState } from "react";
import Link from "next/link";
import { fetchProjectKnowledge } from "@/lib/knowledge";
import type { ProjectKnowledge, KnowledgeType } from "@/types/knowledge";

const TYPE_COLORS: Record<KnowledgeType, string> = {
  pattern: "bg-blue-500/10 text-blue-400",
  decision: "bg-purple-500/10 text-purple-400",
  lesson_learned: "bg-yellow-500/10 text-yellow-400",
  dependency: "bg-cyan-500/10 text-cyan-400",
  best_practice: "bg-emerald-500/10 text-emerald-400",
  architecture: "bg-indigo-500/10 text-indigo-400",
  constraint: "bg-red-500/10 text-red-400",
};

export default function KnowledgePage() {
  const [entries, setEntries] = useState<ProjectKnowledge[]>([]);
  const [total, setTotal] = useState(0);
  const [projectId, setProjectId] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!projectId.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const data = await fetchProjectKnowledge(projectId.trim());
      setEntries(data.items);
      setTotal(data.total);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load knowledge");
    } finally {
      setLoading(false);
    }
  }, [projectId]);

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
        <span className="text-[var(--color-text)]">Knowledge</span>
      </div>

      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Project Knowledge</h1>
        <p className="mt-1 text-sm text-[var(--color-text-muted)]">
          Extracted patterns, decisions, and lessons from project runs
          {total > 0 ? ` (${total} entries)` : ""}
        </p>
      </div>

      {/* Project ID input */}
      <div className="flex gap-3">
        <input
          type="text"
          value={projectId}
          onChange={(e) => setProjectId(e.target.value)}
          placeholder="Enter Project ID…"
          className="flex-1 rounded-lg border border-[var(--color-border)] bg-[var(--color-bg-card)] px-3 py-2 text-sm text-[var(--color-text)] placeholder:text-[var(--color-text-dim)] outline-none focus:border-[var(--color-accent)]"
          onKeyDown={(e) => {
            if (e.key === "Enter") load();
          }}
        />
        <button
          onClick={load}
          disabled={!projectId.trim() || loading}
          className="rounded-lg bg-[var(--color-accent)] px-4 py-2 text-sm font-medium text-white disabled:opacity-50 hover:opacity-90 transition-opacity"
        >
          Load
        </button>
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
      {!loading && entries.length === 0 && projectId.trim() && (
        <div className="rounded-xl border border-dashed border-[var(--color-border)] p-12 text-center">
          <p className="text-sm text-[var(--color-text-muted)]">
            No knowledge entries for this project.
          </p>
        </div>
      )}

      {/* Knowledge list */}
      {!loading && entries.length > 0 && (
        <div className="space-y-3">
          {entries.map((entry) => (
            <div
              key={entry.id}
              className="rounded-xl border border-[var(--color-border)] bg-[var(--color-bg-card)] p-4"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span
                    className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${
                      TYPE_COLORS[entry.knowledge_type] ??
                      "bg-[var(--color-bg-secondary)] text-[var(--color-text-muted)]"
                    }`}
                  >
                    {entry.knowledge_type.replace(/_/g, " ")}
                  </span>
                  <span className="text-sm font-semibold text-[var(--color-text)]">
                    {entry.title}
                  </span>
                </div>
                <div className="flex items-center gap-3 text-xs text-[var(--color-text-muted)]">
                  <span title="Relevance">
                    ⭐ {(entry.relevance_score * 100).toFixed(0)}%
                  </span>
                  <span title="Usage count">↻ {entry.usage_count}</span>
                </div>
              </div>

              <p className="mt-2 text-sm text-[var(--color-text-muted)] line-clamp-3">
                {entry.content}
              </p>

              <div className="mt-3 flex items-center justify-between">
                <div className="flex flex-wrap gap-1.5">
                  {entry.tags?.map((tag) => (
                    <span
                      key={tag}
                      className="rounded bg-[var(--color-bg-secondary)] px-1.5 py-0.5 text-[10px] text-[var(--color-text-muted)]"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
                <span className="text-[10px] text-[var(--color-text-dim)]">
                  {new Date(entry.created_at).toLocaleString()}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
