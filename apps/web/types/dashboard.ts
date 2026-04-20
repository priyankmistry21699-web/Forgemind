/**
 * Dashboard & widget types — matches FM-197 backend contract.
 *
 * Backend source of truth:
 * - apps/api/app/models/analytics_metrics.py (Dashboard, DashboardVisibility)
 * - apps/api/app/services/dashboard_alert_service.py
 *   WIDGET_DATA_SOURCES + WIDGET_CHART_TYPES
 */

export type DashboardVisibility = "private" | "team" | "org";

/**
 * Widget types supported by the backend resolve_widget_data() dispatcher.
 * Keep in sync with WIDGET_DATA_SOURCES in dashboard_alert_service.py.
 */
export type WidgetType =
  | "health_score"
  | "velocity"
  | "quality"
  | "execution_metrics"
  | "debt_summary"
  | "complexity_summary"
  | "flakiness_summary";

/**
 * Chart rendering modes supported by the frontend renderer.
 * Keep in sync with WIDGET_CHART_TYPES in dashboard_alert_service.py.
 */
export type ChartType = "line" | "bar" | "pie" | "table" | "number" | "gauge";

export interface WidgetPosition {
  x: number;
  y: number;
}

export interface WidgetSize {
  w: number;
  h: number;
}

/** Widget configuration stored inside dashboard.layout_json.widgets[]. */
export interface WidgetConfig {
  /** Stable id for React keys and layout targeting. */
  id: string;
  widget_type: WidgetType;
  chart_type: ChartType;
  title?: string;
  position: WidgetPosition;
  size: WidgetSize;
  /** Optional override for the backend data source key. */
  data_source?: string | null;
}

/** Layout JSON persisted on the Dashboard model. */
export interface DashboardLayout {
  widgets: WidgetConfig[];
  /** Grid column count (default 12). */
  columns?: number;
  /** Row height in pixels (default 80). */
  row_height?: number;
}

export interface Dashboard {
  id: string;
  name: string;
  description: string | null;
  layout_json: DashboardLayout;
  visibility: DashboardVisibility;
  created_at?: string;
  updated_at?: string;
}

export interface DashboardListItem {
  id: string;
  name: string;
  visibility: DashboardVisibility;
}

export interface DashboardList {
  total: number;
  items: DashboardListItem[];
}

/**
 * Shape returned by GET /analytics/dashboards/{id}/widgets/{widget_type}.
 * `data` is a normalized metric record whose keys vary by widget_type.
 */
export interface WidgetDataEnvelope {
  widget_type: WidgetType;
  project_id?: string;
  data: Record<string, unknown> | null;
}
