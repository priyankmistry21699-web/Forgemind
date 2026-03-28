"use client";

import { useParams } from "next/navigation";
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Review {
  id: string;
  patch_id: string;
  reviewer_id: string;
  decision: string;
  comment: string | null;
  file_path: string | null;
  line_start: number | null;
  line_end: number | null;
  suggestion: string | null;
  created_at: string;
}

interface Patch {
  id: string;
  project_id: string;
  title: string;
  description: string | null;
  diff_content: string;
  target_branch: string;
  status: string;
  target_files: string[] | null;
  patch_format: string | null;
  readiness_state: string | null;
  created_at: string;
}

function DecisionBadge({ decision }: { decision: string }) {
  const colors: Record<string, string> = {
    approve: "bg-green-500/20 text-green-400",
    request_changes: "bg-amber-500/20 text-amber-400",
    comment: "bg-blue-500/20 text-blue-400",
  };
  return (
    <span
      className={`px-2 py-0.5 rounded text-xs font-medium ${colors[decision] || "bg-gray-500/20 text-gray-400"}`}
    >
      {decision.replace("_", " ")}
    </span>
  );
}

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    draft: "bg-gray-500/20 text-gray-400",
    proposed: "bg-blue-500/20 text-blue-400",
    approved: "bg-green-500/20 text-green-400",
    rejected: "bg-red-500/20 text-red-400",
    applied: "bg-purple-500/20 text-purple-400",
  };
  return (
    <span
      className={`px-2 py-0.5 rounded text-xs font-medium ${colors[status] || "bg-gray-500/20 text-gray-400"}`}
    >
      {status}
    </span>
  );
}

export default function ReviewWorkspacePage() {
  const params = useParams();
  const patchId = params?.patchId as string;

  const [patch, setPatch] = useState<Patch | null>(null);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [patchRes, reviewsRes] = await Promise.all([
        fetch(`${API_BASE}/patches/${patchId}`),
        fetch(`${API_BASE}/patches/${patchId}/reviews`),
      ]);
      if (!patchRes.ok) throw new Error("Patch not found");
      const patchData = await patchRes.json();
      const reviewsData = await reviewsRes.json();
      setPatch(patchData);
      setReviews(reviewsData.items || []);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load review");
    } finally {
      setLoading(false);
    }
  }, [patchId]);

  useEffect(() => {
    load();
  }, [load]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="animate-spin w-6 h-6 border-2 border-[var(--color-accent)] border-t-transparent rounded-full" />
      </div>
    );
  }

  if (error || !patch) {
    return (
      <div className="text-center py-20 text-[var(--color-text-muted)]">
        <p>{error || "Patch not found"}</p>
        <Link
          href="/dashboard"
          className="text-[var(--color-accent)] hover:underline mt-2 inline-block"
        >
          Back to Dashboard
        </Link>
      </div>
    );
  }

  const fileAnnotations = reviews.filter((r) => r.file_path);
  const generalReviews = reviews.filter((r) => !r.file_path);

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-xs text-[var(--color-text-muted)]">
        <Link
          href="/dashboard"
          className="hover:text-[var(--color-text)] transition-colors"
        >
          Dashboard
        </Link>
        <span>/</span>
        <span>Reviews</span>
        <span>/</span>
        <span className="text-[var(--color-text)]">
          {patch.title.slice(0, 40)}
        </span>
      </div>

      {/* Patch Info */}
      <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-6">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-xl font-semibold text-[var(--color-text)]">
              {patch.title}
            </h1>
            {patch.description && (
              <p className="text-sm text-[var(--color-text-muted)] mt-1">
                {patch.description}
              </p>
            )}
          </div>
          <div className="flex items-center gap-2">
            <StatusBadge status={patch.status} />
            {patch.readiness_state && (
              <span className="text-xs text-[var(--color-text-muted)]">
                {patch.readiness_state}
              </span>
            )}
          </div>
        </div>

        <div className="mt-4 flex items-center gap-4 text-xs text-[var(--color-text-muted)]">
          <span>Branch: {patch.target_branch}</span>
          {patch.target_files && (
            <span>{patch.target_files.length} file(s)</span>
          )}
          <span>
            Created: {new Date(patch.created_at).toLocaleDateString()}
          </span>
        </div>

        {/* Target files */}
        {patch.target_files && patch.target_files.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-1">
            {patch.target_files.map((f) => (
              <span
                key={f}
                className="px-2 py-0.5 rounded bg-[var(--color-bg)] text-xs text-[var(--color-text-muted)] border border-[var(--color-border)]"
              >
                {f}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Diff viewer */}
      <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)]">
        <div className="px-4 py-2 border-b border-[var(--color-border)]">
          <h2 className="text-sm font-medium text-[var(--color-text)]">
            Diff
          </h2>
        </div>
        <pre className="p-4 text-xs font-mono text-[var(--color-text-muted)] overflow-x-auto max-h-96 overflow-y-auto whitespace-pre">
          {patch.diff_content}
        </pre>
      </div>

      {/* File-level annotations */}
      {fileAnnotations.length > 0 && (
        <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)]">
          <div className="px-4 py-2 border-b border-[var(--color-border)]">
            <h2 className="text-sm font-medium text-[var(--color-text)]">
              File Annotations ({fileAnnotations.length})
            </h2>
          </div>
          <div className="divide-y divide-[var(--color-border)]">
            {fileAnnotations.map((r) => (
              <div key={r.id} className="p-4">
                <div className="flex items-center gap-2 mb-1">
                  <DecisionBadge decision={r.decision} />
                  <span className="text-xs font-mono text-[var(--color-accent)]">
                    {r.file_path}
                    {r.line_start &&
                      `:${r.line_start}${r.line_end && r.line_end !== r.line_start ? `-${r.line_end}` : ""}`}
                  </span>
                </div>
                {r.comment && (
                  <p className="text-sm text-[var(--color-text-muted)] mt-1">
                    {r.comment}
                  </p>
                )}
                {r.suggestion && (
                  <pre className="mt-2 p-2 rounded bg-green-500/10 text-xs font-mono text-green-400 border border-green-500/20">
                    {r.suggestion}
                  </pre>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* General reviews */}
      <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)]">
        <div className="px-4 py-2 border-b border-[var(--color-border)]">
          <h2 className="text-sm font-medium text-[var(--color-text)]">
            Reviews ({reviews.length})
          </h2>
        </div>
        {generalReviews.length === 0 && fileAnnotations.length === 0 ? (
          <p className="p-4 text-sm text-[var(--color-text-muted)]">
            No reviews yet.
          </p>
        ) : (
          <div className="divide-y divide-[var(--color-border)]">
            {generalReviews.map((r) => (
              <div key={r.id} className="p-4">
                <div className="flex items-center gap-2">
                  <DecisionBadge decision={r.decision} />
                  <span className="text-xs text-[var(--color-text-muted)]">
                    {new Date(r.created_at).toLocaleString()}
                  </span>
                </div>
                {r.comment && (
                  <p className="text-sm text-[var(--color-text)] mt-1">
                    {r.comment}
                  </p>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
