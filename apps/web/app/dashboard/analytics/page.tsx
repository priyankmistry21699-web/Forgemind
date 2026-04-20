"use client";

import { useCallback, useEffect, useState } from "react";
import { ApiError } from "@/lib/api";
import {
  createDashboard,
  deleteDashboard,
  getDashboard,
  listDashboards,
  updateDashboard,
} from "@/lib/dashboards";
import { fetchProjects } from "@/lib/projects";
import type { Project } from "@/types/project";
import type {
  ChartType,
  Dashboard,
  DashboardLayout,
  DashboardListItem,
  WidgetConfig,
  WidgetType,
} from "@/types/dashboard";
import { DashboardGrid } from "@/components/dashboard/dashboard-grid";

const WIDGET_TYPES: WidgetType[] = [
  "health_score",
  "velocity",
  "quality",
  "execution_metrics",
  "debt_summary",
  "complexity_summary",
  "flakiness_summary",
];

const CHART_TYPES: ChartType[] = [
  "line",
  "bar",
  "pie",
  "table",
  "number",
  "gauge",
];

const DEFAULT_LAYOUT: DashboardLayout = {
  columns: 12,
  row_height: 80,
  widgets: [
    {
      id: "w-health",
      widget_type: "health_score",
      chart_type: "gauge",
      title: "Overall Health",
      position: { x: 0, y: 0 },
      size: { w: 3, h: 3 },
    },
    {
      id: "w-velocity",
      widget_type: "velocity",
      chart_type: "number",
      title: "Velocity",
      position: { x: 3, y: 0 },
      size: { w: 3, h: 3 },
    },
    {
      id: "w-quality",
      widget_type: "quality",
      chart_type: "line",
      title: "Quality Trend",
      position: { x: 6, y: 0 },
      size: { w: 6, h: 3 },
    },
    {
      id: "w-debt",
      widget_type: "debt_summary",
      chart_type: "bar",
      title: "Technical Debt",
      position: { x: 0, y: 3 },
      size: { w: 6, h: 4 },
    },
    {
      id: "w-exec",
      widget_type: "execution_metrics",
      chart_type: "pie",
      title: "Execution Breakdown",
      position: { x: 6, y: 3 },
      size: { w: 6, h: 4 },
    },
    {
      id: "w-flaky",
      widget_type: "flakiness_summary",
      chart_type: "table",
      title: "Flaky Tests",
      position: { x: 0, y: 7 },
      size: { w: 12, h: 4 },
    },
  ],
};

function humanize(s: string): string {
  return s
    .split("_")
    .map((w) => w[0].toUpperCase() + w.slice(1))
    .join(" ");
}

export default function AnalyticsDashboardsPage() {
  const [dashboards, setDashboards] = useState<DashboardListItem[]>([]);
  const [listError, setListError] = useState<string | null>(null);
  const [listLoading, setListLoading] = useState(true);

  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [current, setCurrent] = useState<Dashboard | null>(null);
  const [currentError, setCurrentError] = useState<string | null>(null);
  const [currentLoading, setCurrentLoading] = useState(false);

  const [projects, setProjects] = useState<Project[]>([]);
  const [projectId, setProjectId] = useState<string | null>(null);

  const [creating, setCreating] = useState(false);
  const [newName, setNewName] = useState("");
  const [saving, setSaving] = useState(false);
  const [saveMsg, setSaveMsg] = useState<string | null>(null);

  const [addWidgetType, setAddWidgetType] =
    useState<WidgetType>("health_score");
  const [addChartType, setAddChartType] = useState<ChartType>("number");

  const loadDashboards = useCallback(async () => {
    setListLoading(true);
    setListError(null);
    try {
      const res = await listDashboards(0, 100);
      setDashboards(res.items);
      if (res.items.length > 0 && !selectedId) {
        setSelectedId(res.items[0].id);
      }
    } catch (err) {
      setListError(
        err instanceof ApiError ? err.message : "Failed to load dashboards",
      );
    } finally {
      setListLoading(false);
    }
  }, [selectedId]);

  // Initial load: dashboards + projects in parallel.
  useEffect(() => {
    loadDashboards();
    fetchProjects(0, 100)
      .then((res) => {
        setProjects(res.items);
        if (res.items.length > 0) {
          setProjectId(res.items[0].id);
        }
      })
      .catch(() => {
        /* non-fatal — widgets will show "select a project" state */
      });
  }, [loadDashboards]);

  // Load selected dashboard whenever selection changes.
  useEffect(() => {
    if (!selectedId) {
      setCurrent(null);
      return;
    }
    let cancelled = false;
    setCurrentLoading(true);
    setCurrentError(null);
    getDashboard(selectedId)
      .then((d) => {
        if (cancelled) return;
        // Normalize: backend may return null or a non-object for layout_json.
        const layout: DashboardLayout =
          d.layout_json && typeof d.layout_json === "object"
            ? {
                columns: d.layout_json.columns ?? 12,
                row_height: d.layout_json.row_height ?? 80,
                widgets: Array.isArray(d.layout_json.widgets)
                  ? d.layout_json.widgets
                  : [],
              }
            : { columns: 12, row_height: 80, widgets: [] };
        setCurrent({ ...d, layout_json: layout });
      })
      .catch((err) => {
        if (cancelled) return;
        setCurrentError(
          err instanceof ApiError ? err.message : "Failed to load dashboard",
        );
      })
      .finally(() => {
        if (!cancelled) setCurrentLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [selectedId]);

  const handleCreate = async () => {
    const name = newName.trim();
    if (!name) return;
    setCreating(true);
    try {
      const created = await createDashboard({
        name,
        description: null,
        layout_json: DEFAULT_LAYOUT,
        visibility: "private",
      });
      setNewName("");
      await loadDashboards();
      setSelectedId(created.id);
    } catch (err) {
      setListError(
        err instanceof ApiError ? err.message : "Failed to create dashboard",
      );
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async () => {
    if (!current) return;
    if (!window.confirm(`Delete dashboard "${current.name}"?`)) return;
    try {
      await deleteDashboard(current.id);
      setSelectedId(null);
      setCurrent(null);
      await loadDashboards();
    } catch (err) {
      setCurrentError(
        err instanceof ApiError ? err.message : "Failed to delete dashboard",
      );
    }
  };

  const handleSave = async () => {
    if (!current) return;
    setSaving(true);
    setSaveMsg(null);
    try {
      await updateDashboard(current.id, {
        layout_json: current.layout_json,
      });
      setSaveMsg("Saved");
      setTimeout(() => setSaveMsg(null), 2000);
    } catch (err) {
      setSaveMsg(
        err instanceof ApiError ? err.message : "Failed to save layout",
      );
    } finally {
      setSaving(false);
    }
  };

  const handleAddWidget = () => {
    if (!current) return;
    const widgets = current.layout_json.widgets ?? [];
    const maxY = widgets.reduce(
      (m, w) => Math.max(m, (w.position?.y ?? 0) + (w.size?.h ?? 2)),
      0,
    );
    const newWidget: WidgetConfig = {
      id: `w-${Date.now()}`,
      widget_type: addWidgetType,
      chart_type: addChartType,
      title: humanize(addWidgetType),
      position: { x: 0, y: maxY },
      size: { w: 4, h: 3 },
    };
    setCurrent({
      ...current,
      layout_json: {
        ...current.layout_json,
        widgets: [...widgets, newWidget],
      },
    });
  };

  const handleRemoveWidget = (widgetId: string) => {
    if (!current) return;
    setCurrent({
      ...current,
      layout_json: {
        ...current.layout_json,
        widgets: (current.layout_json.widgets ?? []).filter(
          (w) => w.id !== widgetId,
        ),
      },
    });
  };

  return (
    <div className="flex h-full min-h-screen w-full">
      {/* Sidebar: dashboard list */}
      <aside className="flex w-64 shrink-0 flex-col gap-3 border-r border-[var(--color-border)] bg-[var(--color-bg-secondary)] p-4">
        <div>
          <h2 className="text-xs font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">
            Dashboards
          </h2>
          <p className="mt-1 text-[11px] text-[var(--color-text-dim)]">
            FM-197 Custom Analytics
          </p>
        </div>

        <div className="flex gap-2">
          <input
            type="text"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            placeholder="New dashboard name"
            className="min-w-0 flex-1 rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-2 py-1 text-xs text-[var(--color-text)] placeholder-[var(--color-text-dim)] focus:border-[var(--color-accent)] focus:outline-none"
          />
          <button
            type="button"
            onClick={handleCreate}
            disabled={creating || !newName.trim()}
            className="shrink-0 rounded bg-[var(--color-accent)] px-2 py-1 text-xs font-medium text-white hover:bg-[var(--color-accent-hover)] disabled:opacity-50"
          >
            {creating ? "…" : "New"}
          </button>
        </div>

        <div className="flex-1 overflow-auto">
          {listLoading ? (
            <div className="text-xs text-[var(--color-text-dim)]">Loading…</div>
          ) : listError ? (
            <div className="text-xs text-[var(--color-danger)]">
              {listError}
            </div>
          ) : dashboards.length === 0 ? (
            <div className="text-xs text-[var(--color-text-dim)]">
              No dashboards yet. Create one above.
            </div>
          ) : (
            <ul className="flex flex-col gap-1">
              {dashboards.map((d) => (
                <li key={d.id}>
                  <button
                    type="button"
                    onClick={() => setSelectedId(d.id)}
                    className={`w-full truncate rounded px-2 py-1.5 text-left text-xs ${
                      selectedId === d.id
                        ? "bg-[var(--color-accent-glow)] text-[var(--color-text)]"
                        : "text-[var(--color-text-muted)] hover:bg-[var(--color-bg-card-hover)]"
                    }`}
                    title={d.name}
                  >
                    {d.name}
                    <span className="ml-1 text-[10px] text-[var(--color-text-dim)]">
                      · {d.visibility}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </aside>

      {/* Main: header + grid */}
      <main className="flex min-w-0 flex-1 flex-col">
        <header className="flex flex-wrap items-center justify-between gap-3 border-b border-[var(--color-border)] bg-[var(--color-bg-secondary)]/60 px-6 py-4">
          <div className="min-w-0">
            <h1 className="truncate text-lg font-semibold text-[var(--color-text)]">
              {current ? current.name : "Analytics Dashboards"}
            </h1>
            <p className="text-xs text-[var(--color-text-dim)]">
              Custom widget-based views of health, velocity, quality, debt,
              execution, and flakiness metrics.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <label className="flex items-center gap-1 text-xs text-[var(--color-text-muted)]">
              Project
              <select
                value={projectId ?? ""}
                onChange={(e) => setProjectId(e.target.value || null)}
                className="rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-2 py-1 text-xs text-[var(--color-text)]"
              >
                <option value="">—</option>
                {projects.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </select>
            </label>
            {current ? (
              <>
                <button
                  type="button"
                  onClick={handleSave}
                  disabled={saving}
                  className="rounded border border-[var(--color-border)] bg-[var(--color-bg-card)] px-3 py-1 text-xs text-[var(--color-text)] hover:bg-[var(--color-bg-card-hover)] disabled:opacity-50"
                >
                  {saving ? "Saving…" : "Save layout"}
                </button>
                <button
                  type="button"
                  onClick={handleDelete}
                  className="rounded border border-[var(--color-border)] bg-[var(--color-bg-card)] px-3 py-1 text-xs text-[var(--color-danger)] hover:bg-[var(--color-bg-card-hover)]"
                >
                  Delete
                </button>
              </>
            ) : null}
            {saveMsg ? (
              <span className="text-xs text-[var(--color-text-muted)]">
                {saveMsg}
              </span>
            ) : null}
          </div>
        </header>

        {/* Add-widget toolbar */}
        {current ? (
          <div className="flex flex-wrap items-center gap-2 border-b border-[var(--color-border-subtle)] bg-[var(--color-bg)] px-6 py-2 text-xs">
            <span className="text-[var(--color-text-muted)]">Add widget:</span>
            <select
              value={addWidgetType}
              onChange={(e) => setAddWidgetType(e.target.value as WidgetType)}
              className="rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-2 py-1 text-[var(--color-text)]"
            >
              {WIDGET_TYPES.map((t) => (
                <option key={t} value={t}>
                  {humanize(t)}
                </option>
              ))}
            </select>
            <select
              value={addChartType}
              onChange={(e) => setAddChartType(e.target.value as ChartType)}
              className="rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-2 py-1 text-[var(--color-text)]"
            >
              {CHART_TYPES.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
            <button
              type="button"
              onClick={handleAddWidget}
              className="rounded bg-[var(--color-accent)] px-3 py-1 text-white hover:bg-[var(--color-accent-hover)]"
            >
              Add
            </button>
            <span className="ml-auto text-[10px] text-[var(--color-text-dim)]">
              {current.layout_json.widgets.length} widget
              {current.layout_json.widgets.length === 1 ? "" : "s"}
            </span>
          </div>
        ) : null}

        <section className="min-h-0 flex-1 overflow-auto p-6">
          {!selectedId ? (
            <div className="flex h-full items-center justify-center text-sm text-[var(--color-text-dim)]">
              Select a dashboard from the left, or create a new one.
            </div>
          ) : currentLoading ? (
            <div className="flex h-full items-center justify-center text-sm text-[var(--color-text-dim)]">
              Loading dashboard…
            </div>
          ) : currentError ? (
            <div className="flex h-full items-center justify-center text-sm text-[var(--color-danger)]">
              {currentError}
            </div>
          ) : current ? (
            <div className="relative">
              <DashboardGrid
                dashboardId={current.id}
                projectId={projectId}
                layout={current.layout_json}
              />
              {/* Overlay remove buttons for edit mode */}
              {current.layout_json.widgets.length > 0 ? (
                <div className="pointer-events-none absolute inset-0">
                  <div
                    className="grid h-full gap-4"
                    style={{
                      gridTemplateColumns: `repeat(${current.layout_json.columns ?? 12}, minmax(0, 1fr))`,
                      gridAutoRows: `${current.layout_json.row_height ?? 80}px`,
                    }}
                  >
                    {current.layout_json.widgets.map((w) => {
                      const colStart = Math.max(1, (w.position?.x ?? 0) + 1);
                      const rowStart = Math.max(1, (w.position?.y ?? 0) + 1);
                      const colSpan = Math.max(1, w.size?.w ?? 3);
                      const rowSpan = Math.max(1, w.size?.h ?? 2);
                      return (
                        <div
                          key={`rm-${w.id}`}
                          style={{
                            gridColumn: `${colStart} / span ${colSpan}`,
                            gridRow: `${rowStart} / span ${rowSpan}`,
                          }}
                          className="flex justify-end"
                        >
                          <button
                            type="button"
                            onClick={() => handleRemoveWidget(w.id)}
                            className="pointer-events-auto m-1 h-6 w-6 rounded-full bg-[var(--color-bg-secondary)]/80 text-xs text-[var(--color-text-dim)] opacity-0 backdrop-blur-sm transition-opacity hover:bg-[var(--color-danger)] hover:text-white focus:opacity-100 group-hover:opacity-100 hover:opacity-100"
                            aria-label={`Remove ${w.title || w.widget_type}`}
                            title="Remove widget"
                          >
                            ×
                          </button>
                        </div>
                      );
                    })}
                  </div>
                </div>
              ) : null}
            </div>
          ) : null}
        </section>
      </main>
    </div>
  );
}
