import { apiFetch } from "./api";

export interface SLOTarget {
  id: string;
  name: string;
  metric: string;
  threshold: number;
  target_pct: number;
  window_days: number;
}

export interface SLOSummary extends SLOTarget {
  latest_attainment_pct?: number;
  latest_met?: boolean;
}

export interface SLOResult {
  slo_id: string;
  attainment_pct: number;
  met: boolean;
  total_events: number;
  p50: number | null;
  p95: number | null;
  p99: number | null;
}

export async function listSLOs(projectId: string): Promise<SLOSummary[]> {
  const data = await apiFetch(`/projects/${projectId}/slos`);
  return data.items ?? [];
}

export async function createSLO(
  projectId: string,
  body: { name: string; metric: string; threshold: number; target_pct?: number; window_days?: number }
): Promise<SLOTarget> {
  return apiFetch(`/projects/${projectId}/slos`, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function computeSLO(projectId: string, sloId: string): Promise<SLOResult> {
  return apiFetch(`/projects/${projectId}/slos/${sloId}/compute`, { method: "POST" });
}

export async function listAnomalies(
  projectId: string,
  resolved?: boolean
): Promise<unknown[]> {
  const params = resolved !== undefined ? `?resolved=${resolved}` : "";
  const data = await apiFetch(`/projects/${projectId}/anomalies${params}`);
  return data.items ?? [];
}

export async function triggerAnomalyScan(projectId: string): Promise<{ detected: number }> {
  return apiFetch(`/projects/${projectId}/anomalies/scan`, { method: "POST" });
}
