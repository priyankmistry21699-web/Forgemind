"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { fetchProjects } from "@/lib/projects";
import { fetchApprovals } from "@/lib/approvals";
import type { Project } from "@/types/project";
import {
  ProjectCard,
  ProjectListEmpty,
  ProjectListSkeleton,
  ProjectListError,
} from "@/components/projects/project-list";
import { ProjectCreateForm } from "@/components/projects/project-create-form";
import { PromptIntakeForm } from "@/components/planner/prompt-intake-form";
import { PlanningResultCard } from "@/components/planner/planning-result-card";
import { RunTaskList } from "@/components/tasks/run-task-list";
import type { PromptIntakeResponse } from "@/types/planner";

type ActiveForm = "none" | "create" | "prompt";

export default function DashboardPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeForm, setActiveForm] = useState<ActiveForm>("none");
  const [planningResult, setPlanningResult] =
    useState<PromptIntakeResponse | null>(null);
  const [pendingApprovals, setPendingApprovals] = useState(0);
  const formRef = useRef<HTMLDivElement>(null);

  const openForm = useCallback((form: ActiveForm) => {
    setActiveForm(form);
    // Clear stale planning result when re-opening prompt form
    if (form === "prompt") setPlanningResult(null);
    // Scroll form area into view after a tick (for Quick Actions at bottom)
    setTimeout(
      () =>
        formRef.current?.scrollIntoView({
          behavior: "smooth",
          block: "nearest",
        }),
      50,
    );
  }, []);

  const loadProjects = useCallback(() => {
    setLoading(true);
    setError(null);

    Promise.all([fetchProjects(), fetchApprovals({ status: "pending" })])
      .then(([projectData, approvalData]) => {
        setProjects(projectData.items);
        setTotal(projectData.total);
        setPendingApprovals(approvalData.total);
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "Unknown error");
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  useEffect(() => {
    loadProjects();
  }, [loadProjects]);

  return (
    <div className="space-y-8">
      {/* Page header */}
      <div className="flex items-end justify-between gap-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Dashboard</h1>
          <p className="mt-1 text-sm text-[var(--color-text-muted)]">
            Overview of your projects, agents, and platform health.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() =>
              openForm(activeForm === "create" ? "none" : "create")
            }
            className="inline-flex items-center gap-2 rounded-lg bg-[var(--color-accent)] px-4 py-2 text-xs font-medium text-white shadow-md shadow-[var(--color-accent)]/20 transition-all hover:bg-[var(--color-accent-hover)] hover:-translate-y-0.5"
          >
            <svg
              width="12"
              height="12"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.5"
            >
              <line x1="12" y1="5" x2="12" y2="19" />
              <line x1="5" y1="12" x2="19" y2="12" />
            </svg>
            New Project
          </button>
          <button
            onClick={() =>
              openForm(activeForm === "prompt" ? "none" : "prompt")
            }
            className="inline-flex items-center gap-2 rounded-lg border border-[var(--color-accent)]/30 px-4 py-2 text-xs font-medium text-[var(--color-accent)] transition-all hover:border-[var(--color-accent)]/50 hover:bg-[var(--color-accent)]/10"
          >
            <svg
              width="12"
              height="12"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.5"
            >
              <circle cx="11" cy="11" r="8" />
              <line x1="21" y1="21" x2="16.65" y2="16.65" />
            </svg>
            Plan from Prompt
          </button>
        </div>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <div className="group rounded-xl border border-[var(--color-border)] bg-[var(--color-bg-card)] p-5 transition-all hover:border-[var(--color-border-subtle)] hover:bg-[var(--color-bg-card-hover)]">
          <div className="flex items-center justify-between">
            <p className="text-[11px] font-semibold uppercase tracking-wider text-[var(--color-text-dim)]">
              Projects
            </p>
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--color-accent)]/10 text-[var(--color-accent)]">
              <svg
                width="14"
                height="14"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" />
              </svg>
            </div>
          </div>
          <p className="mt-2 text-3xl font-bold tracking-tight">
            {loading ? "—" : String(total)}
          </p>
          <p className="mt-1 text-xs text-[var(--color-text-muted)]">
            {total === 0 && !loading
              ? "Create your first project"
              : `${total} total`}
          </p>
        </div>
        <div className="group rounded-xl border border-[var(--color-border)] bg-[var(--color-bg-card)] p-5 transition-all hover:border-[var(--color-border-subtle)] hover:bg-[var(--color-bg-card-hover)]">
          <div className="flex items-center justify-between">
            <p className="text-[11px] font-semibold uppercase tracking-wider text-[var(--color-text-dim)]">
              Running Agents
            </p>
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-500/10 text-indigo-400">
              <svg
                width="14"
                height="14"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
                <circle cx="9" cy="7" r="4" />
                <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
                <path d="M16 3.13a4 4 0 0 1 0 7.75" />
              </svg>
            </div>
          </div>
          <p className="mt-2 text-3xl font-bold tracking-tight">0</p>
          <p className="mt-1 text-xs text-[var(--color-text-muted)]">Idle</p>
        </div>
        <Link
          href="/dashboard/approvals"
          className="group rounded-xl border border-[var(--color-border)] bg-[var(--color-bg-card)] p-5 transition-all hover:border-[var(--color-warning)]/30 hover:bg-[var(--color-bg-card-hover)]"
        >
          <div className="flex items-center justify-between">
            <p className="text-[11px] font-semibold uppercase tracking-wider text-[var(--color-text-dim)]">
              Pending Approvals
            </p>
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--color-warning)]/10 text-[var(--color-warning)]">
              <svg
                width="14"
                height="14"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                <polyline points="22 4 12 14.01 9 11.01" />
              </svg>
            </div>
          </div>
          <p className="mt-2 text-3xl font-bold tracking-tight">
            {loading ? "—" : String(pendingApprovals)}
          </p>
          <p className="mt-1 text-xs text-[var(--color-text-muted)]">
            {pendingApprovals > 0 ? "Needs attention →" : "All clear"}
          </p>
        </Link>
        <div className="group rounded-xl border border-[var(--color-border)] bg-[var(--color-bg-card)] p-5 transition-all hover:border-[var(--color-border-subtle)] hover:bg-[var(--color-bg-card-hover)]">
          <div className="flex items-center justify-between">
            <p className="text-[11px] font-semibold uppercase tracking-wider text-[var(--color-text-dim)]">
              Health
            </p>
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--color-success)]/10 text-[var(--color-success)]">
              <svg
                width="14"
                height="14"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
              </svg>
            </div>
          </div>
          <p className="mt-2 text-3xl font-bold tracking-tight text-[var(--color-success)]">
            OK
          </p>
          <p className="mt-1 text-xs text-[var(--color-text-muted)]">
            All systems operational
          </p>
        </div>
      </div>

      {/* Inline form area */}
      <div ref={formRef}>
        {activeForm === "create" && (
          <ProjectCreateForm
            onCreated={() => {
              setActiveForm("none");
              loadProjects();
            }}
            onCancel={() => setActiveForm("none")}
          />
        )}

        {activeForm === "prompt" && (
          <PromptIntakeForm
            onPlanned={(result) => {
              setPlanningResult(result);
              setActiveForm("none");
              loadProjects();
            }}
            onCancel={() => setActiveForm("none")}
          />
        )}
      </div>

      {/* Planning result + task list */}
      {planningResult && (
        <div className="space-y-4">
          <PlanningResultCard
            result={planningResult}
            onDismiss={() => setPlanningResult(null)}
          />
          <div>
            <h2 className="mb-3 text-sm font-semibold">Tasks — Latest Run</h2>
            <RunTaskList runId={planningResult.run_id} />
          </div>
        </div>
      )}

      {/* Projects section */}
      <div>
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-sm font-semibold flex items-center gap-2">
            <svg
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              className="text-[var(--color-text-muted)]"
            >
              <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" />
            </svg>
            Projects
          </h2>
          {total > 0 && (
            <span className="rounded-full bg-[var(--color-bg-card)] px-2 py-0.5 text-[11px] font-medium text-[var(--color-text-muted)]">
              {total} project{total !== 1 ? "s" : ""}
            </span>
          )}
        </div>

        {loading && <ProjectListSkeleton />}
        {error && <ProjectListError message={error} />}
        {!loading && !error && projects.length === 0 && <ProjectListEmpty />}
        {!loading && !error && projects.length > 0 && (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {projects.map((project) => (
              <ProjectCard key={project.id} project={project} />
            ))}
          </div>
        )}
      </div>

      {/* Quick actions */}
      <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-bg-card)] p-7">
        <h2 className="mb-5 text-sm font-semibold flex items-center gap-2">
          <svg
            width="14"
            height="14"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="text-[var(--color-accent)]"
          >
            <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
          </svg>
          Quick Actions
        </h2>
        <div className="flex flex-wrap gap-4">
          <button
            onClick={() => openForm("create")}
            className="inline-flex items-center gap-2 rounded-lg bg-[var(--color-accent)] px-5 py-2.5 text-sm font-medium text-white shadow-md shadow-[var(--color-accent)]/20 transition-all hover:bg-[var(--color-accent-hover)] hover:-translate-y-0.5"
          >
            <svg
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <line x1="12" y1="5" x2="12" y2="19" />
              <line x1="5" y1="12" x2="19" y2="12" />
            </svg>
            New Project
          </button>
          <button
            onClick={() => openForm("prompt")}
            className="inline-flex items-center gap-2 rounded-lg border border-[var(--color-accent)]/30 bg-[var(--color-accent-glow)] px-5 py-2.5 text-sm font-medium text-[var(--color-accent)] transition-all hover:border-[var(--color-accent)]/50 hover:bg-[var(--color-accent)]/15 hover:-translate-y-0.5"
          >
            <svg
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <circle cx="11" cy="11" r="8" />
              <line x1="21" y1="21" x2="16.65" y2="16.65" />
            </svg>
            Plan from Prompt
          </button>
          <Link
            href="/dashboard/approvals"
            className="inline-flex items-center gap-2 rounded-lg border border-[var(--color-border)] px-5 py-2.5 text-sm font-medium text-[var(--color-text-muted)] transition-all hover:border-[var(--color-border-subtle)] hover:text-[var(--color-text)] hover:-translate-y-0.5"
          >
            <svg
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
              <polyline points="22 4 12 14.01 9 11.01" />
            </svg>
            Review Approvals
            {pendingApprovals > 0 && (
              <span className="ml-1 rounded-full bg-[var(--color-warning)]/15 px-1.5 py-0.5 text-[10px] font-bold text-[var(--color-warning)]">
                {pendingApprovals}
              </span>
            )}
          </Link>
        </div>
      </div>
    </div>
  );
}
