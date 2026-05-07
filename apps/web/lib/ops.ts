/**
 * FM-220: Ops dashboard data helpers.
 * Fetches admin metrics, LLM costs, security findings, and agent memory.
 */

import { apiFetch } from "@/lib/api";

export interface QueryStat {
  query: string;
  duration_ms: number;
  timestamp: string;
}

export interface CacheStats {
  local_size: number;
  local_max_size: number;
  hits: number;
  misses: number;
  hit_rate: number;
}

export interface JobInfo {
  name: string;
  last_run_at: string | null;
  status: string;
}

export interface ModelRouterStatus {
  models: Record<string, { healthy: boolean; error_count: number; last_error_at: string | null }>;
  config_source: string;
}

export interface LLMCostSummary {
  run_id: string;
  total_cost_usd: number;
  total_prompt_tokens: number;
  total_completion_tokens: number;
  call_count: number;
  by_model: Record<string, { cost_usd: number; calls: number }>;
}

export interface SecurityFinding {
  id: string;
  severity: "low" | "medium" | "high" | "critical";
  source: string;
  title: string;
  file_path: string | null;
  line_number: number | null;
  cwe_id: string | null;
  cve_id: string | null;
  resolved: boolean;
  created_at: string;
}

export async function fetchQueryStats(limit = 20): Promise<QueryStat[]> {
  const data = await apiFetch(`/admin/query-stats?limit=${limit}`);
  return data.queries ?? [];
}

export async function fetchCacheStats(): Promise<CacheStats> {
  return apiFetch("/admin/cache-stats");
}

export async function flushCache(): Promise<void> {
  await apiFetch("/admin/cache-flush", { method: "POST" });
}

export async function fetchJobs(): Promise<JobInfo[]> {
  const data = await apiFetch("/admin/jobs");
  return data.jobs ?? [];
}

export async function triggerJob(jobName: string): Promise<void> {
  await apiFetch(`/admin/jobs/${jobName}/trigger`, { method: "POST" });
}

export async function fetchModelRouterStatus(): Promise<ModelRouterStatus> {
  return apiFetch("/admin/model-router/status");
}

export async function fetchRunLLMCost(runId: string): Promise<LLMCostSummary> {
  return apiFetch(`/runs/${runId}/llm-cost-summary`);
}

export async function fetchSecurityFindings(
  projectId: string,
  opts?: { severity?: string; resolved?: boolean }
): Promise<SecurityFinding[]> {
  const params = new URLSearchParams();
  if (opts?.severity) params.set("severity", opts.severity);
  if (opts?.resolved !== undefined) params.set("resolved", String(opts.resolved));
  const data = await apiFetch(
    `/projects/${projectId}/security-findings?${params.toString()}`
  );
  return data.items ?? [];
}

export async function resolveFinding(
  projectId: string,
  findingId: string
): Promise<void> {
  await apiFetch(
    `/projects/${projectId}/security-findings/${findingId}/resolve`,
    { method: "PATCH" }
  );
}
