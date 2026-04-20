"use client";

import { useEffect, useState } from "react";
import { getWidgetData } from "@/lib/dashboards";
import type { WidgetConfig } from "@/types/dashboard";
import { ApiError } from "@/lib/api";
import { normalizeWidgetData } from "./widget-data-adapter";
import { LineChart } from "./charts/line-chart";
import { BarChart } from "./charts/bar-chart";
import { PieChart } from "./charts/pie-chart";
import { GaugeChart } from "./charts/gauge-chart";
import { StatNumber } from "./charts/stat-number";
import { DataTable } from "./charts/data-table";

interface WidgetRendererProps {
  dashboardId: string;
  projectId: string | null;
  widget: WidgetConfig;
}

type FetchState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "success"; data: Record<string, unknown> | null };

function humanizeWidgetType(type: string): string {
  return type
    .split("_")
    .map((w) => w[0].toUpperCase() + w.slice(1))
    .join(" ");
}

export function WidgetRenderer({
  dashboardId,
  projectId,
  widget,
}: WidgetRendererProps) {
  const [state, setState] = useState<FetchState>({ status: "idle" });

  useEffect(() => {
    if (!projectId) {
      setState({ status: "idle" });
      return;
    }
    let cancelled = false;
    setState({ status: "loading" });
    getWidgetData(dashboardId, widget.widget_type, projectId)
      .then((envelope) => {
        if (cancelled) return;
        setState({ status: "success", data: envelope.data });
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        const message =
          err instanceof ApiError
            ? `${err.status}: ${err.message}`
            : err instanceof Error
              ? err.message
              : "Failed to load widget";
        setState({ status: "error", message });
      });
    return () => {
      cancelled = true;
    };
  }, [dashboardId, projectId, widget.widget_type]);

  const title = widget.title || humanizeWidgetType(widget.widget_type);

  return (
    <section
      className="flex h-full w-full flex-col overflow-hidden rounded-lg border border-[var(--color-border)] bg-[var(--color-bg-card)]"
      aria-label={`${title} widget`}
    >
      <header className="flex shrink-0 items-center justify-between border-b border-[var(--color-border-subtle)] px-3 py-2">
        <h3 className="truncate text-xs font-medium uppercase tracking-wider text-[var(--color-text-muted)]">
          {title}
        </h3>
        <span className="shrink-0 rounded bg-[var(--color-bg-secondary)] px-1.5 py-0.5 text-[10px] text-[var(--color-text-dim)]">
          {widget.chart_type}
        </span>
      </header>
      <div className="min-h-0 flex-1">
        <WidgetBody state={state} projectId={projectId} widget={widget} />
      </div>
    </section>
  );
}

function WidgetBody({
  state,
  projectId,
  widget,
}: {
  state: FetchState;
  projectId: string | null;
  widget: WidgetConfig;
}) {
  if (!projectId) {
    return <Placeholder message="Select a project to load widget data" />;
  }
  if (state.status === "idle" || state.status === "loading") {
    return <Placeholder message="Loading…" shimmer />;
  }
  if (state.status === "error") {
    return (
      <div className="flex h-full w-full flex-col items-center justify-center gap-1 p-4 text-center">
        <span className="text-xs text-[var(--color-danger)]">
          Failed to load
        </span>
        <span className="text-[10px] text-[var(--color-text-dim)]">
          {state.message}
        </span>
      </div>
    );
  }
  const normalized = normalizeWidgetData(widget.widget_type, state.data);
  switch (widget.chart_type) {
    case "line":
      return <LineChart data={normalized.trend} unit={normalized.unit} />;
    case "bar":
      return <BarChart data={normalized.series} unit={normalized.unit} />;
    case "pie":
      return <PieChart data={normalized.series} unit={normalized.unit} />;
    case "gauge":
      return (
        <GaugeChart
          value={normalized.scalar}
          min={normalized.bounds?.[0] ?? 0}
          max={normalized.bounds?.[1] ?? 100}
          label={normalized.scalarLabel}
          unit={normalized.unit}
        />
      );
    case "number":
      return (
        <StatNumber
          value={normalized.scalar}
          label={normalized.scalarLabel}
          unit={normalized.unit}
        />
      );
    case "table":
      return (
        <DataTable
          columns={normalized.table.columns}
          rows={normalized.table.rows}
        />
      );
    default:
      return <Placeholder message={`Unsupported chart: ${widget.chart_type}`} />;
  }
}

function Placeholder({
  message,
  shimmer,
}: {
  message: string;
  shimmer?: boolean;
}) {
  return (
    <div className="flex h-full w-full items-center justify-center">
      <span
        className={`text-xs text-[var(--color-text-dim)] ${shimmer ? "animate-pulse" : ""}`}
      >
        {message}
      </span>
    </div>
  );
}
