import { apiFetch } from "@/lib/api";
import type { GovernancePolicyList, GovernancePolicy } from "@/types/governance";

/** Fetch paginated governance policies. */
export async function fetchGovernancePolicies(
  offset = 0,
  limit = 50,
): Promise<GovernancePolicyList> {
  return apiFetch<GovernancePolicyList>(`/governance/policies?offset=${offset}&limit=${limit}`);
}

/** Fetch a single governance policy by ID. */
export async function fetchGovernancePolicy(policyId: string): Promise<GovernancePolicy> {
  return apiFetch<GovernancePolicy>(`/governance/policies/${policyId}`);
}
