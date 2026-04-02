import { apiFetch } from "@/lib/api";
import type { CostRecordList, CostSummary } from "@/types/cost";

/** Fetch paginated cost records. */
export async function fetchCostRecords(
  offset = 0,
  limit = 50,
): Promise<CostRecordList> {
  return apiFetch<CostRecordList>(`/costs?offset=${offset}&limit=${limit}`);
}

/** Fetch cost summary for a specific run. */
export async function fetchRunCostSummary(runId: string): Promise<CostSummary> {
  return apiFetch<CostSummary>(`/costs/runs/${runId}/summary`);
}

/** Fetch cost summary for a specific project. */
export async function fetchProjectCostSummary(projectId: string): Promise<CostSummary> {
  return apiFetch<CostSummary>(`/costs/projects/${projectId}/summary`);
}

/** Fetch cost breakdown across all records. */
export async function fetchCostBreakdown(): Promise<CostSummary> {
  return apiFetch<CostSummary>(`/costs/breakdown`);
}
