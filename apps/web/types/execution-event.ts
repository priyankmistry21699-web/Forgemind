/** ExecutionEvent types matching the backend ExecutionEventRead schema. */

export type EventType =
  | "task_claimed"
  | "task_completed"
  | "task_failed"
  | "artifact_created"
  | "approval_requested"
  | "approval_resolved"
  | "run_started"
  | "run_completed"
  | "run_failed"
  | "plan_generated";

export interface ExecutionEvent {
  id: string;
  event_type: EventType;
  summary: string;
  metadata_: Record<string, unknown> | null;
  project_id: string | null;
  run_id: string | null;
  task_id: string | null;
  artifact_id: string | null;
  agent_slug: string | null;
  created_at: string;
}

export interface ExecutionEventList {
  items: ExecutionEvent[];
  total: number;
}
