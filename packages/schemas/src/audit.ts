/** Audit export types matching the backend route responses. */

export type AuditEventType =
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

/** Convenience alias used by the web frontend. */
export type EventType = AuditEventType;

export interface AuditSummary {
  total_events: number;
  event_breakdown: Record<string, number>;
  project_id: string | null;
  run_id: string | null;
}

export interface AuditExport {
  events: AuditEvent[];
  metadata: Record<string, unknown>;
}

export interface AuditEvent {
  id: string;
  event_type: AuditEventType;
  task_id: string | null;
  run_id: string | null;
  project_id: string | null;
  payload: Record<string, unknown> | null;
  created_at: string;
}
