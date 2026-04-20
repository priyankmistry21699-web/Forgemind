interface GaugeChartProps {
  value: number | null;
  min?: number;
  max?: number;
  label?: string;
  unit?: string;
}

/**
 * Semicircular gauge. Arc fills from `min` (left) to `max` (right).
 * Colors shift from success → warning → danger as the reading approaches `max`
 * so the same component can express both "higher is better" health scores and
 * "higher is worse" load metrics — the chart just shows where the needle sits.
 */
export function GaugeChart({
  value,
  min = 0,
  max = 100,
  label,
  unit = "",
}: GaugeChartProps) {
  if (value === null || !Number.isFinite(value)) {
    return (
      <div className="flex h-full w-full items-center justify-center text-xs text-[var(--color-text-dim)]">
        No reading available
      </div>
    );
  }

  const clamped = Math.max(min, Math.min(max, value));
  const frac = (clamped - min) / (max - min || 1);

  // 180° arc from (10, 60) to (90, 60) with r=40.
  const cx = 50;
  const cy = 60;
  const r = 40;
  const startAngle = Math.PI; // 180°
  const endAngle = startAngle + frac * Math.PI;
  const fillEnd = {
    x: cx + r * Math.cos(endAngle),
    y: cy + r * Math.sin(endAngle),
  };
  const large = frac > 0.5 ? 1 : 0;
  const bgPath = `M ${cx - r} ${cy} A ${r} ${r} 0 0 1 ${cx + r} ${cy}`;
  const fgPath = `M ${cx - r} ${cy} A ${r} ${r} 0 ${large} 1 ${fillEnd.x.toFixed(3)} ${fillEnd.y.toFixed(3)}`;

  // Color ramp: green → amber → red as frac grows toward 1.
  // This matches conventions for both health scores (invert visually via
  // client choice of min/max) and load/error metrics.
  const color = frac < 0.5
    ? "var(--color-success)"
    : frac < 0.8
      ? "var(--color-warning)"
      : "var(--color-danger)";

  return (
    <div className="flex h-full w-full flex-col items-center justify-center gap-1 p-3">
      <svg
        viewBox="0 0 100 75"
        className="h-full max-h-[140px] w-full"
        role="img"
        aria-label={`Gauge at ${clamped.toFixed(1)}${unit}`}
      >
        <path
          d={bgPath}
          fill="none"
          stroke="var(--color-bg-secondary)"
          strokeWidth={10}
          strokeLinecap="round"
        />
        <path
          d={fgPath}
          fill="none"
          stroke={color}
          strokeWidth={10}
          strokeLinecap="round"
        />
        <text
          x={cx}
          y={cy - 2}
          textAnchor="middle"
          fontSize={14}
          fontWeight={600}
          fill="var(--color-text)"
        >
          {clamped.toFixed(clamped % 1 === 0 ? 0 : 1)}
          {unit}
        </text>
        <text
          x={cx - r}
          y={cy + 12}
          textAnchor="middle"
          fontSize={6}
          fill="var(--color-text-dim)"
        >
          {min}
        </text>
        <text
          x={cx + r}
          y={cy + 12}
          textAnchor="middle"
          fontSize={6}
          fill="var(--color-text-dim)"
        >
          {max}
        </text>
      </svg>
      {label ? (
        <div className="text-center text-[11px] uppercase tracking-wider text-[var(--color-text-dim)]">
          {label}
        </div>
      ) : null}
    </div>
  );
}
