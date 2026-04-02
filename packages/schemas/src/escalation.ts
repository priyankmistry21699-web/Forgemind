/** Escalation types matching the backend schemas. */

export type EscalationTrigger =
  | "task_timeout"
  | "run_failure"
  | "approval_timeout"
  | "budget_exceeded"
  | "trust_score_low"
  | "custom";

export type EscalationAction =
  | "notify"
  | "pause_run"
  | "reassign"
  | "escalate_user"
  | "auto_cancel";

export interface EscalationRule {
  id: string;
  project_id: string;
  name: string;
  trigger: EscalationTrigger;
  action: EscalationAction;
  rules: Record<string, unknown> | null;
  cooldown_minutes: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface EscalationRuleList {
  items: EscalationRule[];
  total: number;
}

export interface EscalationEvent {
  id: string;
  rule_id: string;
  project_id: string;
  trigger: EscalationTrigger;
  action_taken: EscalationAction;
  resource_type: string | null;
  resource_id: string | null;
  metadata_: Record<string, unknown> | null;
  created_at: string;
}

export interface EscalationEventList {
  items: EscalationEvent[];
  total: number;
}
