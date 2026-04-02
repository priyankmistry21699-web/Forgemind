/** Governance policy types matching the backend schemas (FM-047). */

export type PolicyTrigger = "task_type" | "cost_threshold" | "artifact_type" | "agent_action" | "custom";
export type PolicyAction = "require_approval" | "auto_approve" | "block" | "notify";

export interface GovernancePolicy {
  id: string;
  name: string;
  description: string | null;
  trigger: PolicyTrigger;
  action: PolicyAction;
  rules: Record<string, unknown> | null;
  project_id: string | null;
  enabled: boolean;
  priority: number;
  created_at: string;
  updated_at: string;
}

export interface GovernancePolicyList {
  items: GovernancePolicy[];
  total: number;
}
