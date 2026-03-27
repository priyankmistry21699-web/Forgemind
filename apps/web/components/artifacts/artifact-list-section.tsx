"use client";

import Link from "next/link";
import type { Artifact } from "@/types/artifact";

const TYPE_STYLES: Record<string, { bg: string; text: string }> = {
  plan_summary: { bg: "bg-purple-900/50", text: "text-purple-300" },
  architecture: { bg: "bg-cyan-900/50", text: "text-cyan-300" },
  implementation: { bg: "bg-blue-900/50", text: "text-blue-300" },
  review: { bg: "bg-amber-900/50", text: "text-amber-300" },
  test_report: { bg: "bg-green-900/50", text: "text-green-300" },
  documentation: { bg: "bg-indigo-900/50", text: "text-indigo-300" },
  other: { bg: "bg-zinc-700", text: "text-zinc-300" },
};

function ArtifactTypeBadge({ type }: { type: string }) {
  const style = TYPE_STYLES[type] ?? TYPE_STYLES.other;
  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-[11px] font-medium uppercase tracking-wide ${style.bg} ${style.text}`}
    >
      {type.replace("_", " ")}
    </span>
  );
}

interface ArtifactListSectionProps {
  artifacts: Artifact[];
}

export function ArtifactListSection({ artifacts }: ArtifactListSectionProps) {
  if (artifacts.length === 0) {
    return (
      <div className="rounded-xl border border-dashed border-[var(--color-border-subtle)] bg-[var(--color-bg-card)]/50 py-10 text-center">
        <div className="mb-3 text-2xl">\uD83D\uDCC4</div>
        <p className="text-sm font-medium">No artifacts produced yet</p>
        <p className="mt-1 text-xs text-[var(--color-text-muted)]">
          Artifacts will appear here as tasks complete.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {artifacts.map((artifact) => (
        <div
          key={artifact.id}
          className="rounded-xl border border-[var(--color-border)] bg-[var(--color-bg-card)] p-5 transition-all hover:border-[var(--color-border-subtle)] hover:bg-[var(--color-bg-card-hover)]"
        >
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2">
                <Link
                  href={`/dashboard/artifacts/${artifact.id}`}
                  className="truncate text-sm font-medium text-[var(--color-accent)] hover:underline"
                >
                  {artifact.title}
                </Link>
                <ArtifactTypeBadge type={artifact.artifact_type} />
              </div>
              <p className="mt-1 text-xs text-[var(--color-text-muted)]">
                v{artifact.version}
                {artifact.created_by && ` · by ${artifact.created_by}`} ·{" "}
                {new Date(artifact.created_at).toLocaleString()}
              </p>
            </div>
          </div>
          {artifact.content && (
            <pre className="mt-3 max-h-48 overflow-auto rounded-md bg-[var(--color-bg-secondary)] p-3 text-xs text-[var(--color-text-muted)]">
              {artifact.content.slice(0, 2000)}
              {artifact.content.length > 2000 && "\n\n... (truncated)"}
            </pre>
          )}
        </div>
      ))}
    </div>
  );
}
