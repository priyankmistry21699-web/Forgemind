import Link from "next/link";
import type { Project, ProjectStatus } from "@/types/project";

const STATUS_STYLES: Record<ProjectStatus, { bg: string; text: string }> = {
  draft: { bg: "bg-zinc-700", text: "text-zinc-300" },
  planning: { bg: "bg-indigo-900/50", text: "text-indigo-300" },
  active: { bg: "bg-emerald-900/50", text: "text-emerald-300" },
  paused: { bg: "bg-amber-900/50", text: "text-amber-300" },
  completed: { bg: "bg-green-900/50", text: "text-green-300" },
  failed: { bg: "bg-red-900/50", text: "text-red-300" },
};

function StatusBadge({ status }: { status: ProjectStatus }) {
  const style = STATUS_STYLES[status] ?? STATUS_STYLES.draft;
  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-[11px] font-medium uppercase tracking-wide ${style.bg} ${style.text}`}
    >
      {status}
    </span>
  );
}

function timeAgo(dateStr: string): string {
  const seconds = Math.floor((Date.now() - new Date(dateStr).getTime()) / 1000);
  if (seconds < 60) return "just now";
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

export function ProjectCard({ project }: { project: Project }) {
  return (
    <Link
      href={`/dashboard/projects/${project.id}`}
      className="group block rounded-xl border border-[var(--color-border)] bg-[var(--color-bg-card)] p-5 transition-all hover:border-[var(--color-accent)]/30 hover:bg-[var(--color-bg-card-hover)] hover:-translate-y-0.5 hover:shadow-lg hover:shadow-black/20"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <h3 className="truncate text-sm font-semibold group-hover:text-[var(--color-accent)]">
            {project.name}
          </h3>
          {project.description && (
            <p className="mt-1.5 line-clamp-2 text-xs leading-relaxed text-[var(--color-text-muted)]">
              {project.description}
            </p>
          )}
        </div>
        <StatusBadge status={project.status} />
      </div>
      <div className="mt-4 flex items-center gap-2 border-t border-[var(--color-border)]/50 pt-3">
        <svg
          width="11"
          height="11"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          className="text-[var(--color-text-dim)]"
        >
          <circle cx="12" cy="12" r="10" />
          <polyline points="12 6 12 12 16 14" />
        </svg>
        <p className="text-[11px] text-[var(--color-text-dim)]">
          Created {timeAgo(project.created_at)}
        </p>
      </div>
    </Link>
  );
}

export function ProjectListEmpty() {
  return (
    <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-[var(--color-border-subtle)] bg-[var(--color-bg-card)]/50 py-16">
      <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-[var(--color-accent)]/10 text-2xl">
        📁
      </div>
      <p className="text-sm font-semibold">No projects yet</p>
      <p className="mt-1.5 text-xs text-[var(--color-text-muted)]">
        Create your first project to get started.
      </p>
    </div>
  );
}

export function ProjectListSkeleton() {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {[1, 2, 3].map((i) => (
        <div
          key={i}
          className="animate-pulse rounded-lg border border-[var(--color-border)] bg-[var(--color-bg-card)] p-4"
        >
          <div className="mb-2 h-4 w-2/3 rounded bg-[var(--color-bg-secondary)]" />
          <div className="mb-3 h-3 w-full rounded bg-[var(--color-bg-secondary)]" />
          <div className="h-3 w-1/4 rounded bg-[var(--color-bg-secondary)]" />
        </div>
      ))}
    </div>
  );
}

export function ProjectListError({ message }: { message: string }) {
  return (
    <div className="rounded-lg border border-red-900/50 bg-red-950/20 p-4">
      <p className="text-sm font-medium text-red-400">
        Failed to load projects
      </p>
      <p className="mt-1 text-xs text-red-400/70">{message}</p>
    </div>
  );
}
