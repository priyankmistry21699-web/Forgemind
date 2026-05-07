import { apiFetch } from "./api";

export interface BudgetForecast {
  project_id: string;
  forecast_month: string;
  actual_spend_usd: number;
  forecasted_spend_usd: number;
  budget_usd: number | null;
  burn_rate_usd_per_day: number;
  days_remaining: number;
  will_exceed_budget: boolean;
  confidence: number;
  breakdown_by_agent: Record<string, number> | null;
}

export interface CostAttribution {
  run_id: string;
  total_cost_usd: number;
  total_calls: number;
  by_task_type: Record<string, { cost_usd: number; calls: number }>;
}

export async function getCostForecast(
  projectId: string,
  budgetUsd?: number
): Promise<BudgetForecast> {
  const params = budgetUsd !== undefined ? `?budget_usd=${budgetUsd}` : "";
  return apiFetch(`/projects/${projectId}/cost-forecast${params}`);
}

export async function getRunCostAttribution(runId: string): Promise<CostAttribution> {
  return apiFetch(`/runs/${runId}/cost-attribution`);
}
