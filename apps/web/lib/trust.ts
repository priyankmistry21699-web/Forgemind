import { apiFetch } from "@/lib/api";
import type { TrustScoreList, RiskSummary } from "@/types/trust";

/** Fetch paginated trust scores. */
export async function fetchTrustScores(
  offset = 0,
  limit = 50,
): Promise<TrustScoreList> {
  return apiFetch<TrustScoreList>(`/trust/scores?offset=${offset}&limit=${limit}`);
}

/** Fetch risk summary for a specific run. */
export async function fetchRunRiskSummary(runId: string): Promise<RiskSummary> {
  return apiFetch<RiskSummary>(`/trust/runs/${runId}/risk-summary`);
}
