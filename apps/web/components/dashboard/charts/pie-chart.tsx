import type { SeriesPoint } from "../widget-data-adapter";

interface PieChartProps {
  data: SeriesPoint[];
  unit?: string;
}

/** A palette with strong contrast on the dark theme. Cycled by slice index. */
const PALETTE = [
  "#6366f1", // accent (indigo)
  "#22c55e", // success
  "#f59e0b", // warning
  "#ef4444", // danger
  "#06b6d4", // cyan
  "#a855f7", // purple
  "#84cc16", // lime
  "#ec4899", // pink
];

/**
 * Convert polar coordinates to Cartesian for arc path math.
 * Angles are clockwise from 12 o'clock (standard pie layout).
 */
function polar(cx: number, cy: number, r: number, angleRad: number) {
  return {
    x: cx + r * Math.sin(angleRad),
    y: cy - r * Math.cos(angleRad),
  };
}

export function PieChart({ data, unit = "" }: PieChartProps) {
  const positive = data.filter((d) => d.value > 0);
  if (positive.length === 0) {
    return (
      <div className="flex h-full w-full items-center justify-center text-xs text-[var(--color-text-dim)]">
        No values to chart
      </div>
    );
  }

  const total = positive.reduce((s, d) => s + d.value, 0);
  const cx = 50;
  const cy = 50;
  const r = 40;

  // Single slice: render as a full circle (SVG arcs cannot cover 360°).
  if (positive.length === 1) {
    const d = positive[0];
    return (
      <div className="flex h-full w-full items-center gap-4 p-3">
        <svg viewBox="0 0 100 100" className="h-full max-h-full max-w-[50%]">
          <circle cx={cx} cy={cy} r={r} fill={PALETTE[0]}>
            <title>{`${d.label}: ${d.value}${unit} (100%)`}</title>
          </circle>
        </svg>
        <Legend data={positive} total={total} unit={unit} />
      </div>
    );
  }

  let cursor = 0;
  const slices = positive.map((d, i) => {
    const frac = d.value / total;
    const startAngle = cursor * 2 * Math.PI;
    cursor += frac;
    const endAngle = cursor * 2 * Math.PI;
    const start = polar(cx, cy, r, startAngle);
    const end = polar(cx, cy, r, endAngle);
    const large = frac > 0.5 ? 1 : 0;
    const path = [
      `M ${cx} ${cy}`,
      `L ${start.x.toFixed(3)} ${start.y.toFixed(3)}`,
      `A ${r} ${r} 0 ${large} 1 ${end.x.toFixed(3)} ${end.y.toFixed(3)}`,
      "Z",
    ].join(" ");
    return { path, color: PALETTE[i % PALETTE.length], ...d, frac };
  });

  return (
    <div className="flex h-full w-full items-center gap-4 overflow-hidden p-3">
      <svg
        viewBox="0 0 100 100"
        className="h-full max-h-full max-w-[50%]"
        role="img"
        aria-label={`Pie chart with ${positive.length} slices`}
      >
        {slices.map((s, i) => (
          <path key={i} d={s.path} fill={s.color}>
            <title>{`${s.label}: ${s.value}${unit} (${(s.frac * 100).toFixed(1)}%)`}</title>
          </path>
        ))}
      </svg>
      <Legend data={positive} total={total} unit={unit} />
    </div>
  );
}

function Legend({
  data,
  total,
  unit,
}: {
  data: SeriesPoint[];
  total: number;
  unit: string;
}) {
  return (
    <ul className="flex min-w-0 flex-1 flex-col gap-1 overflow-auto text-[11px]">
      {data.map((d, i) => {
        const pct = (d.value / total) * 100;
        return (
          <li key={i} className="flex items-center gap-2">
            <span
              className="h-2.5 w-2.5 shrink-0 rounded-sm"
              style={{ backgroundColor: PALETTE[i % PALETTE.length] }}
            />
            <span className="flex-1 truncate text-[var(--color-text-muted)]">
              {d.label}
            </span>
            <span className="shrink-0 tabular-nums text-[var(--color-text)]">
              {pct.toFixed(1)}%{unit ? ` ${unit}` : ""}
            </span>
          </li>
        );
      })}
    </ul>
  );
}
