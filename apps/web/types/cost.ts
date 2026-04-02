/** Cost tracking types matching the backend schemas (FM-047/cost tracking). */

export interface CostRecord {
  id: string;
  model_name: string;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  cost_usd: number;
  project_id: string | null;
  run_id: string | null;
  task_id: string | null;
  caller: string;
  created_at: string;
}

export interface CostRecordList {
  items: CostRecord[];
  total: number;
}

export interface CostSummary {
  total_cost_usd: number;
  total_tokens: number;
  record_count: number;
  by_model: Record<string, { cost_usd: number; tokens: number; count: number }>;
}
