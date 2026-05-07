interface StatNumberProps {
  value: number | null;
  label?: string;
  unit?: string;
  /** Optional delta shown below the value (e.g. from previous period). */
  delta?: number | null;
}

/** Large single-number widget with optional label + delta indicator. */
export function StatNumber({
  value,
  label,
  unit = "",
  delta,
}: StatNumberProps) {
  if (value === null || !Number.isFinite(value)) {
    return (
      <div className="flex h-full w-full items-center justify-center text-xs text-[var(--color-text-dim)]">
        No value
      </div>
    );
  }
  const formatted =
    Math.abs(value) >= 1000
      ? value.toLocaleString(undefined, { maximumFractionDigits: 0 })
      : value.toFixed(value % 1 === 0 ? 0 : 2);

  const deltaColor =
    delta === null || delta === undefined
      ? null
      : delta > 0
        ? "var(--color-success)"
        : delta < 0
          ? "var(--color-danger)"
          : "var(--color-text-dim)";

  return (
    <div className="flex h-full w-full flex-col items-center justify-center gap-1 p-4 text-center">
      <div className="text-4xl font-semibold tabular-nums text-[var(--color-text)]">
        {formatted}
        {unit ? (
          <span className="ml-1 text-xl text-[var(--color-text-muted)]">
            {unit}
          </span>
        ) : null}
      </div>
      {label ? (
        <div className="text-[11px] uppercase tracking-wider text-[var(--color-text-dim)]">
          {label}
        </div>
      ) : null}
      {deltaColor && delta !== null && delta !== undefined ? (
        <div
          className="mt-1 text-xs tabular-nums"
          style={{ color: deltaColor }}
        >
          {delta > 0 ? "▲" : delta < 0 ? "▼" : "–"} {Math.abs(delta).toFixed(2)}
        </div>
      ) : null}
    </div>
  );
}
