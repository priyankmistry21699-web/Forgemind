import type { PromptIntakeResponse } from "@/types/planner";

interface PlanningResultCardProps {
  result: PromptIntakeResponse;
  onDismiss: () => void;
}

export function PlanningResultCard({
  result,
  onDismiss,
}: PlanningResultCardProps) {
  return (
    <div className="rounded-lg border border-emerald-900/50 bg-emerald-950/20 p-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-medium text-emerald-400">
            Project planned successfully
          </p>
          <p className="mt-1 text-xs text-emerald-400/70">{result.message}</p>
        </div>
        <button
          onClick={onDismiss}
          className="text-xs text-[var(--color-text-muted)] hover:text-[var(--color-text)] transition-colors"
        >
          ✕
        </button>
      </div>
      <div className="mt-3 flex flex-wrap gap-4 text-xs text-[var(--color-text-muted)]">
        <span>
          Tasks created:{" "}
          <strong className="text-[var(--color-text)]">
            {result.tasks_created}
          </strong>
        </span>
        <span className="truncate" title={result.project_id}>
          Project:{" "}
          <code className="text-[11px]">{result.project_id.slice(0, 8)}…</code>
        </span>
        <span className="truncate" title={result.run_id}>
          Run: <code className="text-[11px]">{result.run_id.slice(0, 8)}…</code>
        </span>
      </div>
    </div>
  );
}
