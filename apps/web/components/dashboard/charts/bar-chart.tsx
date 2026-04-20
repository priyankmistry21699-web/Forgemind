import type { SeriesPoint } from "../widget-data-adapter";

interface BarChartProps {
  data: SeriesPoint[];
  unit?: string;
}

/** Horizontal bar chart — easier to label than vertical for long categorical labels. */
export function BarChart({ data, unit = "" }: BarChartProps) {
  if (data.length === 0) {
    return (
      <div className="flex h-full w-full items-center justify-center text-xs text-[var(--color-text-dim)]">
        No categories to display
      </div>
    );
  }
  const max = Math.max(...data.map((d) => d.value), 0) || 1;

  return (
    <div className="flex h-full w-full flex-col gap-1.5 overflow-auto p-3">
      {data.map((d, i) => {
        const pct = Math.max(0, (d.value / max) * 100);
        return (
          <div key={i} className="flex flex-col gap-0.5">
            <div className="flex items-center justify-between text-[11px]">
              <span
                className="truncate pr-2 text-[var(--color-text-muted)]"
                title={d.label}
              >
                {d.label}
              </span>
              <span className="shrink-0 tabular-nums text-[var(--color-text)]">
                {d.value.toFixed(d.value >= 100 ? 0 : 2)}
                {unit}
              </span>
            </div>
            <div className="h-2 w-full overflow-hidden rounded-sm bg-[var(--color-bg-secondary)]">
              <div
                className="h-full rounded-sm bg-[var(--color-accent)] transition-all"
                style={{ width: `${pct}%` }}
                role="progressbar"
                aria-valuenow={d.value}
                aria-valuemin={0}
                aria-valuemax={max}
                aria-label={d.label}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}
