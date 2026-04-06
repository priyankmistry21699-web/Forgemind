"use client";

import { useCallback, useEffect, useState } from "react";
import {
  fetchSuggestions,
  generateSuggestions,
  resolveSuggestion,
} from "@/lib/constitution-suggestions";
import type { ConstitutionSuggestion } from "@forgemind/types";

interface ConstitutionSuggestionsProps {
  projectId: string;
}

export function ConstitutionSuggestions({
  projectId,
}: ConstitutionSuggestionsProps) {
  const [items, setItems] = useState<ConstitutionSuggestion[]>([]);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [resolvingId, setResolvingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetchSuggestions(projectId, "pending");
      setItems(res.items);
    } catch {
      /* ignore */
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    load();
  }, [load]);

  async function handleGenerate() {
    setGenerating(true);
    setError(null);
    try {
      const res = await generateSuggestions(projectId);
      setItems(res.items);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Generation failed");
    } finally {
      setGenerating(false);
    }
  }

  async function handleResolve(
    id: string,
    action: "accept" | "reject",
  ) {
    setResolvingId(id);
    setError(null);
    try {
      await resolveSuggestion(projectId, id, action);
      setItems((prev) => prev.filter((s) => s.id !== id));
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to resolve");
    } finally {
      setResolvingId(null);
    }
  }

  return (
    <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-bg-card)] p-4">
      <div className="mb-3 flex items-center justify-between">
        <h4 className="text-sm font-semibold text-[var(--color-text)]">
          Constitution Suggestions
        </h4>
        <button
          onClick={handleGenerate}
          disabled={generating}
          className="rounded-lg bg-[var(--color-accent)] px-3 py-1.5 text-xs font-medium text-white transition-all hover:bg-[var(--color-accent-hover)] disabled:opacity-50"
        >
          {generating ? "Analyzing…" : "Generate"}
        </button>
      </div>

      {error && <p className="mb-3 text-xs text-red-400">{error}</p>}

      {loading ? (
        <p className="text-xs text-[var(--color-text-muted)]">Loading…</p>
      ) : items.length === 0 ? (
        <p className="text-xs text-[var(--color-text-muted)]">
          No pending suggestions. Click Generate to analyze project history.
        </p>
      ) : (
        <div className="space-y-3">
          {items.map((s) => (
            <div
              key={s.id}
              className="rounded-lg border border-[var(--color-border)] bg-[var(--color-bg-secondary)] p-3"
            >
              <p className="mb-1 text-xs font-semibold text-[var(--color-text)]">
                {s.title}
              </p>
              {s.rationale && (
                <p className="mb-2 text-xs text-[var(--color-text-muted)]">
                  {s.rationale}
                </p>
              )}
              <pre className="mb-2 whitespace-pre-wrap rounded bg-[var(--color-bg-card)] p-2 text-xs text-[var(--color-text)]">
                {s.suggested_text}
              </pre>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => handleResolve(s.id, "accept")}
                  disabled={resolvingId === s.id}
                  className="rounded bg-green-600 px-3 py-1 text-xs font-medium text-white transition-colors hover:bg-green-500 disabled:opacity-50"
                >
                  Accept
                </button>
                <button
                  onClick={() => handleResolve(s.id, "reject")}
                  disabled={resolvingId === s.id}
                  className="rounded border border-[var(--color-border)] px-3 py-1 text-xs text-[var(--color-text-muted)] transition-colors hover:text-[var(--color-text)] disabled:opacity-50"
                >
                  Reject
                </button>
                {s.category && (
                  <span className="ml-auto text-[10px] text-[var(--color-text-muted)]">
                    {s.category}
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
