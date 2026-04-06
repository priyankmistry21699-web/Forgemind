/** Phase Agent Profile types matching backend schemas. */

export type WorkflowPhase =
  | "specify"
  | "plan"
  | "tasks"
  | "implement"
  | "review"
  | "validate";

export interface PhaseAgentProfile {
  id: string;
  project_id: string;
  phase: WorkflowPhase;
  agent_id: string;
  priority: number;
  is_default: boolean;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface PhaseAgentProfileCreate {
  phase: WorkflowPhase;
  agent_id: string;
  priority?: number;
  is_default?: boolean;
  notes?: string | null;
}

export interface PhaseAgentProfileList {
  items: PhaseAgentProfile[];
  total: number;
}
