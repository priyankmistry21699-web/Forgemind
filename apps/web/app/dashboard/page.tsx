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
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Dashboard</h1>
          <p className="mt-1 text-sm text-[var(--color-text-muted)]">
            Overview of your projects, agents, and platform health.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() =>
              openForm(activeForm === "create" ? "none" : "create")
            }
            className="rounded-md bg-[var(--color-accent)] px-3 py-1.5 text-xs font-medium text-white transition-colors hover:bg-[var(--color-accent-hover)]"
          >
            + New Project
          </button>
          <button
            onClick={() =>
              openForm(activeForm === "prompt" ? "none" : "prompt")
            }
            className="rounded-md border border-[var(--color-accent)] px-3 py-1.5 text-xs font-medium text-[var(--color-accent)] transition-colors hover:bg-[var(--color-accent)] hover:text-white"
          >
            Plan from Prompt
          </button>
        </div>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-bg-card)] p-4">
          <p className="text-xs font-medium uppercase tracking-wide text-[var(--color-text-muted)]">
            Projects
          </p>
          <p className="mt-1 text-2xl font-bold">
            {loading ? "—" : String(total)}
          </p>
          <p className="mt-0.5 text-xs text-[var(--color-text-muted)]">
            {total === 0 && !loading
              ? "Create your first project"
              : `${total} total`}
          </p>
        </div>
        <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-bg-card)] p-4">
          <p className="text-xs font-medium uppercase tracking-wide text-[var(--color-text-muted)]">
            Running Agents
          </p>
          <p className="mt-1 text-2xl font-bold">0</p>
          <p className="mt-0.5 text-xs text-[var(--color-text-muted)]">Idle</p>
        </div>
        <Link
          href="/dashboard/approvals"
          className="rounded-lg border border-[var(--color-border)] bg-[var(--color-bg-card)] p-4 transition-colors hover:border-[var(--color-accent)]"
        >
          <p className="text-xs font-medium uppercase tracking-wide text-[var(--color-text-muted)]">
            Pending Approvals
          </p>
          <p className="mt-1 text-2xl font-bold">
            {loading ? "—" : String(pendingApprovals)}
          </p>
          <p className="mt-0.5 text-xs text-[var(--color-text-muted)]">
            {pendingApprovals > 0 ? "Needs attention →" : "All clear"}
          </p>
        </Link>
        <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-bg-card)] p-4">
          <p className="text-xs font-medium uppercase tracking-wide text-[var(--color-text-muted)]">
            Health
          </p>
          <p className="mt-1 text-2xl font-bold">OK</p>
          <p className="mt-0.5 text-xs text-[var(--color-text-muted)]">
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
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-sm font-semibold">Projects</h2>
          {total > 0 && (
            <span className="text-xs text-[var(--color-text-muted)]">
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
      <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-bg-card)] p-6">
        <h2 className="mb-3 text-sm font-semibold">Quick Actions</h2>
        <div className="flex flex-wrap gap-3">
          <button
            onClick={() => openForm("create")}
            className="rounded-md border border-[var(--color-accent)] px-4 py-2 text-sm text-[var(--color-accent)] transition-colors hover:bg-[var(--color-accent)] hover:text-white"
          >
            New Project
          </button>
          <button
            onClick={() => openForm("prompt")}
            className="rounded-md border border-[var(--color-accent)] px-4 py-2 text-sm text-[var(--color-accent)] transition-colors hover:bg-[var(--color-accent)] hover:text-white"
          >
            Plan from Prompt
          </button>
          <Link
            href="/dashboard/approvals"
            className="rounded-md border border-[var(--color-border)] px-4 py-2 text-sm text-[var(--color-text)] transition-colors hover:border-[var(--color-accent)] hover:text-[var(--color-accent)]"
          >
            Review Approvals
            {pendingApprovals > 0 && (
              <span className="ml-1.5 rounded-full bg-amber-900/50 px-1.5 py-0.5 text-[10px] text-amber-300">
                {pendingApprovals}
              </span>
            )}
          </Link>
        </div>
      </div>
    </div>
  );
}
