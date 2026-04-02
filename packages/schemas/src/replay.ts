/** Replay snapshot types matching the backend schemas (FM-046). */

export interface ReplaySnapshot {
  id: string;
  task_id: string;
  run_id: string;
  project_id: string;
  agent_slug: string;
  input_snapshot: Record<string, unknown> | null;
  prompt_snapshot: string | null;
  model_used: string | null;
  temperature: number | null;
  output_snapshot: Record<string, unknown> | null;
  error: string | null;
  tokens_used: number;
  duration_ms: number;
  cost_usd: number;
  replay_hash: string | null;
  is_replay: boolean;
  original_snapshot_id: string | null;
  sequence_number: number;
  created_at: string;
}

export interface ReplaySnapshotList {
  items: ReplaySnapshot[];
  total: number;
}

export interface ExecutionTrace {
  run_id: string;
  total_steps: number;
  snapshots: ReplaySnapshot[];
  total_tokens: number;
  total_cost_usd: number;
  total_duration_ms: number;
}
