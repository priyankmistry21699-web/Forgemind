import type { SeriesPoint } from "../widget-data-adapter";

interface LineChartProps {
  data: SeriesPoint[];
  /** Optional unit suffix shown in tooltips via <title>. */
  unit?: string;
}

/** Minimalist pure-SVG line chart with axis baseline + value dots. */
export function LineChart({ data, unit = "" }: LineChartProps) {
  if (data.length === 0) {
    return <EmptyChart label="No data points" />;
  }
  if (data.length === 1) {
    // Degenerate: one point → render as stat, not a line.
    return (
      <div className="flex h-full w-full items-center justify-center text-[var(--color-text)]">
        <span className="text-3xl font-semibold tabular-nums">
          {data[0].value.toFixed(1)}
          {unit}
        </span>
      </div>
    );
  }

  const width = 100;
  const height = 40;
  const padX = 2;
  const padY = 4;
  const values = data.map((d) => d.value);
  const max = Math.max(...values);
  const min = Math.min(...values);
  const range = max - min || 1;

  const xStep = (width - padX * 2) / (data.length - 1);
  const points = data.map((d, i) => {
    const x = padX + i * xStep;
    const y = height - padY - ((d.value - min) / range) * (height - padY * 2);
    return { x, y, ...d };
  });

  const path = points
    .map((p, i) => `${i === 0 ? "M" : "L"} ${p.x.toFixed(2)} ${p.y.toFixed(2)}`)
    .join(" ");
  const areaPath = `${path} L ${points[points.length - 1].x.toFixed(2)} ${height - padY} L ${padX} ${height - padY} Z`;

  return (
    <div className="flex h-full w-full flex-col gap-2 p-3">
      <svg
        viewBox={`0 0 ${width} ${height}`}
        preserveAspectRatio="none"
        className="h-full w-full"
        role="img"
        aria-label={`Line chart with ${data.length} points`}
      >
        <path d={areaPath} fill="var(--color-accent-glow)" stroke="none" />
        <path
          d={path}
          fill="none"
          stroke="var(--color-accent)"
          strokeWidth={0.8}
          strokeLinejoin="round"
          strokeLinecap="round"
          vectorEffect="non-scaling-stroke"
        />
        {points.map((p, i) => (
          <circle
            key={i}
            cx={p.x}
            cy={p.y}
            r={0.8}
            fill="var(--color-accent)"
            vectorEffect="non-scaling-stroke"
          >
            <title>{`${p.label}: ${p.value.toFixed(2)}${unit}`}</title>
          </circle>
        ))}
      </svg>
      <div className="flex justify-between text-[10px] text-[var(--color-text-dim)]">
        <span>{data[0].label}</span>
        <span>{data[data.length - 1].label}</span>
      </div>
    </div>
  );
}

function EmptyChart({ label }: { label: string }) {
  return (
    <div className="flex h-full w-full items-center justify-center text-xs text-[var(--color-text-dim)]">
      {label}
    </div>
  );
}
