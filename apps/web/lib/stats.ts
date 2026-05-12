import { apiFetch } from "@/lib/api";

export interface StatsOverview {
  running_tasks: number;
  pending_approvals: number;
  healthy: boolean;
  db_latency_ms: number | null;
}

export async function fetchStatsOverview(): Promise<StatsOverview> {
  return apiFetch<StatsOverview>("/stats/overview");
}
