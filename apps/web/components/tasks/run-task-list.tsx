"use client";

import { useEffect, useState } from "react";
import { fetchTasksByRun, retryTask, cancelTask } from "@/lib/tasks";
import type { Task, TaskStatus } from "@/types/task";

const STATUS_STYLES: Record<
  TaskStatus,
  { bg: string; text: string; dot: string }
> = {
  pending: { bg: "bg-zinc-700", text: "text-zinc-300", dot: "bg-zinc-400" },
  blocked: {
    bg: "bg-amber-900/50",
    text: "text-amber-300",
    dot: "bg-amber-400",
  },
  ready: {
    bg: "bg-indigo-900/50",
    text: "text-indigo-300",
    dot: "bg-indigo-400",
  },
  running: { bg: "bg-blue-900/50", text: "text-blue-300", dot: "bg-blue-400" },
  completed: {
    bg: "bg-green-900/50",
    text: "text-green-300",
    dot: "bg-green-400",
  },
  failed: { bg: "bg-red-900/50", text: "text-red-300", dot: "bg-red-400" },
  skipped: { bg: "bg-zinc-800", text: "text-zinc-500", dot: "bg-zinc-500" },
};

function TaskStatusBadge({ status }: { status: TaskStatus }) {
  const style = STATUS_STYLES[status] ?? STATUS_STYLES.pending;
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-[11px] font-medium uppercase tracking-wide ${style.bg} ${style.text}`}
    >
      <span className={`inline-block h-1.5 w-1.5 rounded-full ${style.dot}`} />
      {status}
    </span>
  );
}

interface TaskItemProps {
  task: Task;
  onAction?: () => void;
}

function TaskItem({ task, onAction }: TaskItemProps) {
  const isBlocked = task.status === "blocked";
  const isReady = task.status === "ready";
  const isFailed = task.status === "failed";
  const isRunning = task.status === "running";
  const [acting, setActing] = useState(false);

  async function handleRetry() {
    setActing(true);
    try {
      await retryTask(task.id);
      onAction?.();
    } catch {
      /* swallow — user sees status unchanged */
    } finally {
      setActing(false);
    }
  }

  async function handleCancel() {
    setActing(true);
    try {
      await cancelTask(task.id);
      onAction?.();
    } catch {
      /* swallow */
    } finally {
      setActing(false);
    }
  }

  return (
    <div
      className={`flex items-center justify-between gap-3 rounded-md border px-4 py-3 ${
        isReady
          ? "border-indigo-800/50 bg-indigo-950/20"
          : isBlocked
            ? "border-amber-800/30 bg-amber-950/10"
            : "border-[var(--color-border)] bg-[var(--color-bg-card)]"
      }`}
    >
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <span className="text-[11px] text-[var(--color-text-muted)]">
            #{task.order_index + 1}
          </span>
          <h4 className="truncate text-sm font-medium">{task.title}</h4>
        </div>
        {task.description && (
          <p className="mt-0.5 truncate text-xs text-[var(--color-text-muted)]">
            {task.description}
          </p>
        )}
        {task.depends_on && task.depends_on.length > 0 && (
          <p className="mt-1 text-[11px] text-[var(--color-text-muted)]">
            Depends on {task.depends_on.length} task
            {task.depends_on.length !== 1 ? "s" : ""}
          </p>
        )}
        {task.error_message && (
          <p className="mt-1 text-[11px] text-red-400 truncate">
            {task.error_message}
          </p>
        )}
      </div>
      <div className="flex shrink-0 items-center gap-2">
        {isFailed && (
          <button
            disabled={acting}
            onClick={handleRetry}
            className="rounded px-2 py-1 text-[11px] font-medium text-indigo-400 border border-indigo-800/50 hover:bg-indigo-900/30 transition-colors disabled:opacity-50"
          >
            Retry
          </button>
        )}
        {(isReady || isRunning) && (
          <button
            disabled={acting}
            onClick={handleCancel}
            className="rounded px-2 py-1 text-[11px] font-medium text-red-400 border border-red-800/50 hover:bg-red-900/30 transition-colors disabled:opacity-50"
          >
            Cancel
          </button>
        )}
        <span className="text-[11px] text-[var(--color-text-muted)]">
          {task.task_type}
        </span>
        <TaskStatusBadge status={task.status} />
      </div>
    </div>
  );
}

interface RunTaskListProps {
  runId: string;
}

export function RunTaskList({ runId }: RunTaskListProps) {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    fetchTasksByRun(runId)
      .then((data) => {
        if (!cancelled) {
          setTasks(data.items);
          setTotal(data.total);
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load tasks");
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [runId, refreshKey]);

  if (loading) {
    return (
      <div className="space-y-2">
        {[1, 2, 3].map((i) => (
          <div
            key={i}
            className="animate-pulse rounded-md border border-[var(--color-border)] bg-[var(--color-bg-card)] p-4"
          >
            <div className="h-4 w-2/3 rounded bg-[var(--color-bg-secondary)]" />
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg border border-red-900/50 bg-red-950/20 p-4">
        <p className="text-sm font-medium text-red-400">Failed to load tasks</p>
        <p className="mt-1 text-xs text-red-400/70">{error}</p>
      </div>
    );
  }

  if (tasks.length === 0) {
    return (
      <p className="text-xs text-[var(--color-text-muted)]">
        No tasks in this run.
      </p>
    );
  }

  const readyCount = tasks.filter((t) => t.status === "ready").length;
  const completedCount = tasks.filter((t) => t.status === "completed").length;

  return (
    <div>
      <div className="mb-2 flex items-center justify-between">
        <span className="text-xs text-[var(--color-text-muted)]">
          {total} task{total !== 1 ? "s" : ""}
        </span>
        <div className="flex gap-3 text-[11px] text-[var(--color-text-muted)]">
          {readyCount > 0 && (
            <span className="text-indigo-400">{readyCount} ready</span>
          )}
          {completedCount > 0 && (
            <span className="text-green-400">{completedCount} completed</span>
          )}
        </div>
      </div>
      <div className="space-y-2">
        {tasks.map((task) => (
          <TaskItem
            key={task.id}
            task={task}
            onAction={() => setRefreshKey((k) => k + 1)}
          />
        ))}
      </div>
    </div>
  );
}
