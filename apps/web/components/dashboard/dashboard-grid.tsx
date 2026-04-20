"use client";

import { WidgetRenderer } from "./widget-renderer";
import type { DashboardLayout } from "@/types/dashboard";

interface DashboardGridProps {
  dashboardId: string;
  projectId: string | null;
  layout: DashboardLayout;
}

/**
 * CSS Grid layout engine for dashboard widgets. Each widget's `position`
 * and `size` (grid units) are translated directly into grid-column/row
 * spans so the layout persisted by the backend renders identically here.
 */
export function DashboardGrid({
  dashboardId,
  projectId,
  layout,
}: DashboardGridProps) {
  const widgets = layout.widgets ?? [];
  const columns = layout.columns ?? 12;
  const rowHeight = layout.row_height ?? 80;

  if (widgets.length === 0) {
    return (
      <div className="flex h-64 items-center justify-center rounded-lg border border-dashed border-[var(--color-border)] bg-[var(--color-bg-card)]/40 text-sm text-[var(--color-text-dim)]">
        This dashboard has no widgets yet.
      </div>
    );
  }

  return (
    <div
      className="grid gap-4"
      style={{
        gridTemplateColumns: `repeat(${columns}, minmax(0, 1fr))`,
        gridAutoRows: `${rowHeight}px`,
      }}
    >
      {widgets.map((w) => {
        const colStart = Math.max(1, (w.position?.x ?? 0) + 1);
        const rowStart = Math.max(1, (w.position?.y ?? 0) + 1);
        const colSpan = Math.max(1, w.size?.w ?? 3);
        const rowSpan = Math.max(1, w.size?.h ?? 2);
        return (
          <div
            key={w.id}
            style={{
              gridColumn: `${colStart} / span ${colSpan}`,
              gridRow: `${rowStart} / span ${rowSpan}`,
            }}
          >
            <WidgetRenderer
              dashboardId={dashboardId}
              projectId={projectId}
              widget={w}
            />
          </div>
        );
      })}
    </div>
  );
}
