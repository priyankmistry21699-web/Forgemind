/** Task types matching the backend TaskRead schema. */

export type TaskStatus =
  | "pending"
  | "blocked"
  | "ready"
  | "running"
  | "completed"
  | "failed"
  | "skipped";

export interface Task {
  id: string;
  title: string;
  description: string | null;
  task_type: string;
  status: TaskStatus;
  order_index: number;
  depends_on: string[] | null;
  parent_id: string | null;
  run_id: string;
  assigned_agent_slug: string | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface TaskList {
  items: Task[];
  total: number;
}
