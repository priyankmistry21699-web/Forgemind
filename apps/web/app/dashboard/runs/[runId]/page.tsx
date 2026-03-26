"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";

import { fetchRun } from "@/lib/runs";
import { fetchTasksByRun } from "@/lib/tasks";
import { fetchArtifacts } from "@/lib/artifacts";
import { fetchApprovals } from "@/lib/approvals";
import { fetchEvents } from "@/lib/events";
import { fetchProject } from "@/lib/projects";

import type { Run } from "@/types/run";
import type { Project } from "@/types/project";
import type { Task } from "@/types/task";
import type { Artifact } from "@/types/artifact";
import type { Approval } from "@/types/approval";
import type { ExecutionEvent } from "@/types/execution-event";

import { ArtifactListSection } from "@/components/artifacts/artifact-list-section";
import { ApprovalListSection } from "@/components/approvals/approval-list-section";
import { EventTimelineSection } from "@/components/events/event-timeline-section";
import { RunTaskList } from "@/components/tasks/run-task-list";
import { RunChatPanel } from "@/components/chat/run-chat-panel";

const RUN_STATUS_STYLES: Record<string, { bg: string; text: string }> = {
  pending: { bg: "bg-zinc-700", text: "text-zinc-300" },
  planning: { bg: "bg-indigo-900/50", text: "text-indigo-300" },
  running: { bg: "bg-blue-900/50", text: "text-blue-300" },
  paused: { bg: "bg-amber-900/50", text: "text-amber-300" },
  completed: { bg: "bg-green-900/50", text: "text-green-300" },
  failed: { bg: "bg-red-900/50", text: "text-red-300" },
};

function StatusBadge({ status }: { status: string }) {
  const style = RUN_STATUS_STYLES[status] ?? {
    bg: "bg-zinc-700",
    text: "text-zinc-300",
  };
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

export default function RunDetailPage() {
  const params = useParams<{ runId: string }>();
  const runId = params.runId;

  const [run, setRun] = useState<Run | null>(null);
  const [project, setProject] = useState<Project | null>(null);
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  const [approvals, setApprovals] = useState<Approval[]>([]);
  const [events, setEvents] = useState<ExecutionEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const runData = await fetchRun(runId);
      setRun(runData);

      const [projectData, artifactData, approvalData, eventData] =
        await Promise.all([
          fetchProject(runData.project_id),
          fetchArtifacts(runData.project_id, runId),
          fetchApprovals({ runId }),
          fetchEvents({ runId }),
        ]);

      setProject(projectData);
      setArtifacts(artifactData.items);
      setApprovals(approvalData.items);
      setEvents(eventData.items);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load run");
    } finally {
      setLoading(false);
    }
  }, [runId]);

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

  if (error || !run) {
    return (
      <div className="space-y-4">
        <Link
          href="/dashboard"
          className="text-xs text-[var(--color-accent)] hover:underline"
        >
          ← Back to Dashboard
        </Link>
        <div className="rounded-lg border border-red-900/50 bg-red-950/20 p-4">
          <p className="text-sm font-medium text-red-400">Failed to load run</p>
          <p className="mt-1 text-xs text-red-400/70">
            {error ?? "Run not found"}
          </p>
        </div>
      </div>
    );
  }

  const pendingApprovals = approvals.filter((a) => a.status === "pending");

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
        <span className="text-[var(--color-text)]">Run #{run.run_number}</span>
      </div>

      {/* Run header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">
            Run #{run.run_number}
          </h1>
          <p className="mt-1 text-sm text-[var(--color-text-muted)]">
            Triggered by {run.trigger} · {formatDate(run.created_at)}
          </p>
        </div>
        <StatusBadge status={run.status} />
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-bg-card)] p-4">
          <p className="text-xs font-medium uppercase tracking-wide text-[var(--color-text-muted)]">
            Status
          </p>
          <p className="mt-1 text-sm font-semibold capitalize">{run.status}</p>
        </div>
        <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-bg-card)] p-4">
          <p className="text-xs font-medium uppercase tracking-wide text-[var(--color-text-muted)]">
            Artifacts
          </p>
          <p className="mt-1 text-sm font-semibold">{artifacts.length}</p>
        </div>
        <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-bg-card)] p-4">
          <p className="text-xs font-medium uppercase tracking-wide text-[var(--color-text-muted)]">
            Approvals
          </p>
          <p className="mt-1 text-sm font-semibold">
            {pendingApprovals.length > 0 ? (
              <span className="text-amber-400">
                {pendingApprovals.length} pending
              </span>
            ) : (
              approvals.length
            )}
          </p>
        </div>
        <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-bg-card)] p-4">
          <p className="text-xs font-medium uppercase tracking-wide text-[var(--color-text-muted)]">
            Events
          </p>
          <p className="mt-1 text-sm font-semibold">{events.length}</p>
        </div>
      </div>

      {/* Tasks */}
      <div>
        <h2 className="mb-3 text-sm font-semibold">Tasks</h2>
        <RunTaskList runId={runId} />
      </div>

      {/* Artifacts */}
      <div>
        <h2 className="mb-3 text-sm font-semibold">
          Artifacts
          <span className="ml-2 text-xs font-normal text-[var(--color-text-muted)]">
            {artifacts.length}
          </span>
        </h2>
        <ArtifactListSection artifacts={artifacts} />
      </div>

      {/* Approvals */}
      <div>
        <h2 className="mb-3 text-sm font-semibold">
          Approvals
          {pendingApprovals.length > 0 && (
            <span className="ml-2 rounded-full bg-amber-900/50 px-1.5 py-0.5 text-[10px] font-medium text-amber-300">
              {pendingApprovals.length} pending
            </span>
          )}
        </h2>
        <ApprovalListSection approvals={approvals} />
      </div>

      {/* Event Timeline */}
      <div>
        <h2 className="mb-3 text-sm font-semibold">
          Event Timeline
          <span className="ml-2 text-xs font-normal text-[var(--color-text-muted)]">
            {events.length}
          </span>
        </h2>
        <EventTimelineSection events={events} />
      </div>

      {/* Execution Chat */}
      <div>
        <h2 className="mb-3 text-sm font-semibold">Execution Assistant</h2>
        <RunChatPanel runId={runId} />
      </div>
    </div>
  );
}
