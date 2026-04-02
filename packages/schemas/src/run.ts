/** Run types matching the backend RunRead schema. */

export type RunStatus =
  | "pending"
  | "planning"
  | "running"
  | "paused"
  | "completed"
  | "failed";

export interface Run {
  id: string;
  run_number: number;
  status: RunStatus;
  trigger: string;
  project_id: string;
  created_at: string;
  updated_at: string;
}

export interface RunList {
  items: Run[];
  total: number;
}
