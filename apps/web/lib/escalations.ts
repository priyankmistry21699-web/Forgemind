import { apiFetch } from "@/lib/api";
import type { EscalationRule, EscalationRuleList, EscalationEventList } from "@/types/escalation";

/** Fetch escalation rules for a project. */
export async function fetchEscalationRules(
  projectId: string,
  offset = 0,
  limit = 50,
): Promise<EscalationRuleList> {
  return apiFetch<EscalationRuleList>(
    `/projects/${projectId}/escalation/rules?offset=${offset}&limit=${limit}`,
  );
}

/** Create an escalation rule. */
export async function createEscalationRule(
  projectId: string,
  data: {
    name: string;
    trigger: string;
    action: string;
    rules?: Record<string, unknown>;
    cooldown_minutes?: number;
  },
): Promise<EscalationRule> {
  return apiFetch<EscalationRule>(
    `/projects/${projectId}/escalation/rules`,
    { method: "POST", body: JSON.stringify(data) },
  );
}

/** Update an escalation rule. */
export async function updateEscalationRule(
  ruleId: string,
  data: Partial<{
    name: string;
    trigger: string;
    action: string;
    rules: Record<string, unknown>;
    cooldown_minutes: number;
    is_active: boolean;
  }>,
): Promise<EscalationRule> {
  return apiFetch<EscalationRule>(`/escalation/rules/${ruleId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

/** Fetch escalation events for a project. */
export async function fetchEscalationEvents(
  projectId: string,
  offset = 0,
  limit = 50,
): Promise<EscalationEventList> {
  return apiFetch<EscalationEventList>(
    `/projects/${projectId}/escalation/events?offset=${offset}&limit=${limit}`,
  );
}
