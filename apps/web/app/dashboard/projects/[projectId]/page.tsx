"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { fetchProject, fetchLatestRun } from "@/lib/projects";
import { fetchArtifacts } from "@/lib/artifacts";
import { fetchApprovals } from "@/lib/approvals";
import type { Project } from "@/types/project";
import type { Run } from "@/types/run";
import type { Artifact } from "@/types/artifact";
import type { Approval } from "@/types/approval";
import { RunTaskList } from "@/components/tasks/run-task-list";
import { PlannerResultView } from "@/components/planner/planner-result-view";
import { ArtifactListSection } from "@/components/artifacts/artifact-list-section";
import { ApprovalListSection } from "@/components/approvals/approval-list-section";

const STATUS_STYLES: Record<string, { bg: string; text: string }> = {
  draft: { bg: "bg-zinc-700", text: "text-zinc-300" },
  planning: { bg: "bg-indigo-900/50", text: "text-indigo-300" },
  active: { bg: "bg-emerald-900/50", text: "text-emerald-300" },
  paused: { bg: "bg-amber-900/50", text: "text-amber-300" },
  completed: { bg: "bg-green-900/50", text: "text-green-300" },
  failed: { bg: "bg-red-900/50", text: "text-red-300" },
};

const RUN_STATUS_STYLES: Record<string, { bg: string; text: string }> = {
  pending: { bg: "bg-zinc-700", text: "text-zinc-300" },
  planning: { bg: "bg-indigo-900/50", text: "text-indigo-300" },
  running: { bg: "bg-blue-900/50", text: "text-blue-300" },
  paused: { bg: "bg-amber-900/50", text: "text-amber-300" },
  completed: { bg: "bg-green-900/50", text: "text-green-300" },
  failed: { bg: "bg-red-900/50", text: "text-red-300" },
};

function StatusBadge({
  status,
  styles,
}: {
  status: string;
  styles: Record<string, { bg: string; text: string }>;
}) {
  const style = styles[status] ?? { bg: "bg-zinc-700", text: "text-zinc-300" };
  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-[11px] font-medium uppercase tracking-wide ${style.bg} ${style.text}`}
    >
      {status}
    </span>
  );
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleString();
}

export default function ProjectDetailPage() {
  const params = useParams<{ projectId: string }>();
  const projectId = params.projectId;

  const [project, setProject] = useState<Project | null>(null);
  const [latestRun, setLatestRun] = useState<Run | null>(null);
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  const [approvals, setApprovals] = useState<Approval[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [proj, run] = await Promise.all([
        fetchProject(projectId),
        fetchLatestRun(projectId),
      ]);
      setProject(proj);
      setLatestRun(run);

      if (run) {
        const [artData, appData] = await Promise.all([
          fetchArtifacts(projectId, run.id),
          fetchApprovals({ runId: run.id }),
        ]);
        setArtifacts(artData.items);
        setApprovals(appData.items);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load project");
    } finally {
      setLoading(false);
    }
  }, [projectId]);

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
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="animate-pulse rounded-lg border border-[var(--color-border)] bg-[var(--color-bg-card)] p-4"
            >
              <div className="h-4 w-1/2 rounded bg-[var(--color-bg-secondary)]" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error || !project) {
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
            Failed to load project
          </p>
          <p className="mt-1 text-xs text-red-400/70">
            {error ?? "Project not found"}
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
        <span className="text-[var(--color-text)]">{project.name}</span>
      </div>

      {/* Project header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">{project.name}</h1>
          {project.description && (
            <p className="mt-1 text-sm text-[var(--color-text-muted)]">
              {project.description}
            </p>
          )}
        </div>
        <StatusBadge status={project.status} styles={STATUS_STYLES} />
      </div>

      {/* Project metadata */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-bg-card)] p-4">
          <p className="text-xs font-medium uppercase tracking-wide text-[var(--color-text-muted)]">
            Status
          </p>
          <p className="mt-1 text-sm font-semibold capitalize">
            {project.status}
          </p>
        </div>
        <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-bg-card)] p-4">
          <p className="text-xs font-medium uppercase tracking-wide text-[var(--color-text-muted)]">
            Created
          </p>
          <p className="mt-1 text-sm font-semibold">
            {formatDate(project.created_at)}
          </p>
        </div>
        <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-bg-card)] p-4">
          <p className="text-xs font-medium uppercase tracking-wide text-[var(--color-text-muted)]">
            Last Updated
          </p>
          <p className="mt-1 text-sm font-semibold">
            {formatDate(project.updated_at)}
          </p>
        </div>
      </div>

      {/* Latest run */}
      <div>
        <h2 className="mb-3 text-sm font-semibold">Latest Run</h2>
        {latestRun ? (
          <div className="space-y-4">
            <div className="flex items-center gap-3 rounded-lg border border-[var(--color-border)] bg-[var(--color-bg-card)] p-4">
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <Link
                    href={`/dashboard/runs/${latestRun.id}`}
                    className="text-sm font-medium text-[var(--color-accent)] hover:underline"
                  >
                    Run #{latestRun.run_number}
                  </Link>
                  <StatusBadge
                    status={latestRun.status}
                    styles={RUN_STATUS_STYLES}
                  />
                </div>
                <p className="mt-1 text-xs text-[var(--color-text-muted)]">
                  Triggered by {latestRun.trigger} ·{" "}
                  {formatDate(latestRun.created_at)}
                </p>
              </div>
            </div>
            <RunTaskList runId={latestRun.id} />
          </div>
        ) : (
          <div className="rounded-lg border border-dashed border-[var(--color-border)] py-8 text-center">
            <p className="text-sm text-[var(--color-text-muted)]">
              No runs yet
            </p>
            <p className="mt-1 text-xs text-[var(--color-text-muted)]">
              Submit a planning prompt from the dashboard to create the first
              run.
            </p>
          </div>
        )}
      </div>

      {/* Planning result */}
      {latestRun && (
        <div>
          <h2 className="mb-3 text-sm font-semibold">Planning Result</h2>
          <PlannerResultView runId={latestRun.id} />
        </div>
      )}

      {/* Artifacts */}
      {latestRun && artifacts.length > 0 && (
        <div>
          <h2 className="mb-3 text-sm font-semibold">
            Artifacts
            <span className="ml-2 text-xs font-normal text-[var(--color-text-muted)]">
              {artifacts.length}
            </span>
          </h2>
          <ArtifactListSection artifacts={artifacts} />
        </div>
      )}

      {/* Approvals */}
      {latestRun && approvals.length > 0 && (
        <div>
          <h2 className="mb-3 text-sm font-semibold">
            Approvals
            {approvals.filter((a) => a.status === "pending").length > 0 && (
              <span className="ml-2 rounded-full bg-amber-900/50 px-1.5 py-0.5 text-[10px] font-medium text-amber-300">
                {approvals.filter((a) => a.status === "pending").length} pending
              </span>
            )}
          </h2>
          <ApprovalListSection approvals={approvals} />
        </div>
      )}
    </div>
  );
}
