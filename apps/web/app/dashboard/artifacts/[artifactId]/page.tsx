"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";

import { fetchArtifact } from "@/lib/artifacts";
import { fetchProject } from "@/lib/projects";
import { fetchRun } from "@/lib/runs";

import type { Artifact } from "@/types/artifact";
import type { Project } from "@/types/project";
import type { Run } from "@/types/run";

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
      {type.replace(/_/g, " ")}
    </span>
  );
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleString();
}

export default function ArtifactDetailPage() {
  const params = useParams<{ artifactId: string }>();
  const artifactId = params.artifactId;

  const [artifact, setArtifact] = useState<Artifact | null>(null);
  const [project, setProject] = useState<Project | null>(null);
  const [run, setRun] = useState<Run | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const art = await fetchArtifact(artifactId);
      setArtifact(art);

      const fetches: Promise<void>[] = [];

      fetches.push(fetchProject(art.project_id).then((p) => setProject(p)));

      if (art.run_id) {
        fetches.push(fetchRun(art.run_id).then((r) => setRun(r)));
      }

      await Promise.all(fetches);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load artifact");
    } finally {
      setLoading(false);
    }
  }, [artifactId]);

  useEffect(() => {
    load();
  }, [load]);

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse">
          <div className="h-6 w-1/3 rounded bg-[var(--color-bg-secondary)]" />
          <div className="mt-2 h-4 w-2/3 rounded bg-[var(--color-bg-secondary)]" />
        </div>
        <div className="animate-pulse rounded-lg border border-[var(--color-border)] bg-[var(--color-bg-card)] p-6">
          <div className="h-64 rounded bg-[var(--color-bg-secondary)]" />
        </div>
      </div>
    );
  }

  if (error || !artifact) {
    return (
      <div className="space-y-4">
        <Link
          href="/dashboard"
          className="text-xs text-[var(--color-accent)] hover:underline"
        >
          ← Back to Dashboard
        </Link>
        <div className="rounded-lg border border-red-900/50 bg-red-950/20 p-4">
          <p className="text-sm font-medium text-red-400">
            Failed to load artifact
          </p>
          <p className="mt-1 text-xs text-red-400/70">
            {error ?? "Artifact not found"}
          </p>
        </div>
      </div>
    );
  }

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
        {project && (
          <>
            <Link
              href={`/dashboard/projects/${project.id}`}
              className="hover:text-[var(--color-text)] transition-colors"
            >
              {project.name}
            </Link>
            <span>/</span>
          </>
        )}
        {run && (
          <>
            <Link
              href={`/dashboard/runs/${run.id}`}
              className="hover:text-[var(--color-text)] transition-colors"
            >
              Run #{run.run_number}
            </Link>
            <span>/</span>
          </>
        )}
        <span className="text-[var(--color-text)]">{artifact.title}</span>
      </div>

      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">
            {artifact.title}
          </h1>
          <p className="mt-1 text-sm text-[var(--color-text-muted)]">
            Created {formatDate(artifact.created_at)}
            {artifact.created_by && ` by ${artifact.created_by}`}
          </p>
        </div>
        <ArtifactTypeBadge type={artifact.artifact_type} />
      </div>

      {/* Metadata cards */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-bg-card)] p-4">
          <p className="text-xs font-medium uppercase tracking-wide text-[var(--color-text-muted)]">
            Type
          </p>
          <p className="mt-1 text-sm font-semibold capitalize">
            {artifact.artifact_type.replace(/_/g, " ")}
          </p>
        </div>
        <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-bg-card)] p-4">
          <p className="text-xs font-medium uppercase tracking-wide text-[var(--color-text-muted)]">
            Version
          </p>
          <p className="mt-1 text-sm font-semibold">v{artifact.version}</p>
        </div>
        <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-bg-card)] p-4">
          <p className="text-xs font-medium uppercase tracking-wide text-[var(--color-text-muted)]">
            Created By
          </p>
          <p className="mt-1 text-sm font-semibold">
            {artifact.created_by ?? "—"}
          </p>
        </div>
        <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-bg-card)] p-4">
          <p className="text-xs font-medium uppercase tracking-wide text-[var(--color-text-muted)]">
            Last Updated
          </p>
          <p className="mt-1 text-sm font-semibold">
            {formatDate(artifact.updated_at)}
          </p>
        </div>
      </div>

      {/* Links */}
      <div className="flex flex-wrap gap-3">
        {project && (
          <Link
            href={`/dashboard/projects/${project.id}`}
            className="rounded-md border border-[var(--color-border)] px-3 py-1.5 text-xs text-[var(--color-text-muted)] transition-colors hover:border-[var(--color-accent)] hover:text-[var(--color-accent)]"
          >
            Project: {project.name}
          </Link>
        )}
        {run && (
          <Link
            href={`/dashboard/runs/${run.id}`}
            className="rounded-md border border-[var(--color-border)] px-3 py-1.5 text-xs text-[var(--color-text-muted)] transition-colors hover:border-[var(--color-accent)] hover:text-[var(--color-accent)]"
          >
            Run #{run.run_number}
          </Link>
        )}
        {artifact.task_id && (
          <span className="rounded-md border border-[var(--color-border)] px-3 py-1.5 text-xs text-[var(--color-text-muted)]">
            Task: {artifact.task_id.slice(0, 8)}…
          </span>
        )}
      </div>

      {/* Metadata JSON */}
      {artifact.meta && Object.keys(artifact.meta).length > 0 && (
        <div>
          <h2 className="mb-3 text-sm font-semibold">Metadata</h2>
          <pre className="rounded-lg border border-[var(--color-border)] bg-[var(--color-bg-secondary)] p-4 text-xs text-[var(--color-text-muted)] overflow-auto max-h-48">
            {JSON.stringify(artifact.meta, null, 2)}
          </pre>
        </div>
      )}

      {/* Content */}
      <div>
        <h2 className="mb-3 text-sm font-semibold">Content</h2>
        {artifact.content ? (
          <pre className="rounded-lg border border-[var(--color-border)] bg-[var(--color-bg-secondary)] p-4 text-sm text-[var(--color-text)] overflow-auto whitespace-pre-wrap leading-relaxed">
            {artifact.content}
          </pre>
        ) : (
          <div className="rounded-lg border border-dashed border-[var(--color-border)] py-8 text-center">
            <p className="text-sm text-[var(--color-text-muted)]">
              No content available
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
