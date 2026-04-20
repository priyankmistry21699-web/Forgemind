import { apiFetch } from "@/lib/api";
import type {
  Dashboard,
  DashboardLayout,
  DashboardList,
  DashboardVisibility,
  WidgetDataEnvelope,
  WidgetType,
} from "@/types/dashboard";

/** List dashboards visible to the current user. */
export async function listDashboards(
  offset = 0,
  limit = 50,
): Promise<DashboardList> {
  return apiFetch<DashboardList>(
    `/analytics/dashboards?limit=${limit}&offset=${offset}`,
  );
}

/** Fetch a single dashboard by id. */
export async function getDashboard(id: string): Promise<Dashboard> {
  return apiFetch<Dashboard>(`/analytics/dashboards/${id}`);
}

export interface CreateDashboardInput {
  name: string;
  description?: string | null;
  layout_json?: DashboardLayout;
  visibility?: DashboardVisibility;
  org_id?: string | null;
}

/** Backend mutation response for create/update (id + name only). */
export interface DashboardMutationResult {
  id: string;
  name: string;
}

/** Create a new dashboard. Returns `{id, name}`; fetch full record via getDashboard. */
export async function createDashboard(
  input: CreateDashboardInput,
): Promise<DashboardMutationResult> {
  return apiFetch<DashboardMutationResult>("/analytics/dashboards", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export interface UpdateDashboardInput {
  name?: string;
  description?: string | null;
  layout_json?: DashboardLayout;
  visibility?: DashboardVisibility;
}

/** Update an existing dashboard. Returns `{id, name}`. */
export async function updateDashboard(
  id: string,
  input: UpdateDashboardInput,
): Promise<DashboardMutationResult> {
  return apiFetch<DashboardMutationResult>(`/analytics/dashboards/${id}`, {
    method: "PUT",
    body: JSON.stringify(input),
  });
}

/** Delete a dashboard. */
export async function deleteDashboard(id: string): Promise<void> {
  await apiFetch<{ deleted: boolean }>(`/analytics/dashboards/${id}`, {
    method: "DELETE",
  });
}

/**
 * Resolve widget data for a given dashboard + widget_type + project.
 * Calls GET /analytics/dashboards/{id}/widgets/{widget_type}?project_id=...
 */
export async function getWidgetData(
  dashboardId: string,
  widgetType: WidgetType,
  projectId: string,
): Promise<WidgetDataEnvelope> {
  const qs = new URLSearchParams({ project_id: projectId }).toString();
  return apiFetch<WidgetDataEnvelope>(
    `/analytics/dashboards/${dashboardId}/widgets/${widgetType}?${qs}`,
  );
}
