import { apiFetch } from "@/lib/api";
import type { AuditSummary, AuditExport, EventType } from "@/types/audit";

/** Fetch audit summary with optional filters. */
export async function fetchAuditSummary(params?: {
  project_id?: string;
  run_id?: string;
  event_type?: EventType;
  start_date?: string;
  end_date?: string;
}): Promise<AuditSummary> {
  const qs = new URLSearchParams();
  if (params?.project_id) qs.set("project_id", params.project_id);
  if (params?.run_id) qs.set("run_id", params.run_id);
  if (params?.event_type) qs.set("event_type", params.event_type);
  if (params?.start_date) qs.set("start_date", params.start_date);
  if (params?.end_date) qs.set("end_date", params.end_date);
  const query = qs.toString();
  return apiFetch<AuditSummary>(`/audit/summary${query ? `?${query}` : ""}`);
}

/** Export audit events as JSON. */
export async function exportAuditJson(params?: {
  project_id?: string;
  run_id?: string;
  event_type?: EventType;
  start_date?: string;
  end_date?: string;
}): Promise<AuditExport> {
  const qs = new URLSearchParams();
  if (params?.project_id) qs.set("project_id", params.project_id);
  if (params?.run_id) qs.set("run_id", params.run_id);
  if (params?.event_type) qs.set("event_type", params.event_type);
  if (params?.start_date) qs.set("start_date", params.start_date);
  if (params?.end_date) qs.set("end_date", params.end_date);
  const query = qs.toString();
  return apiFetch<AuditExport>(`/audit/export/json${query ? `?${query}` : ""}`);
}

/** Export audit events as CSV (returns raw text). */
export async function exportAuditCsv(params?: {
  project_id?: string;
  run_id?: string;
  event_type?: EventType;
  start_date?: string;
  end_date?: string;
}): Promise<string> {
  const qs = new URLSearchParams();
  if (params?.project_id) qs.set("project_id", params.project_id);
  if (params?.run_id) qs.set("run_id", params.run_id);
  if (params?.event_type) qs.set("event_type", params.event_type);
  if (params?.start_date) qs.set("start_date", params.start_date);
  if (params?.end_date) qs.set("end_date", params.end_date);
  const query = qs.toString();
  return apiFetch<string>(`/audit/export/csv${query ? `?${query}` : ""}`);
}
