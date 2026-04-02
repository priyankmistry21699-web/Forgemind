import { apiFetch } from "@/lib/api";
import type { AgentList, Agent } from "@/types/agent";

/** Fetch all registered agents. */
export async function fetchAgents(): Promise<AgentList> {
  return apiFetch<AgentList>("/agents");
}

/** Fetch a single agent by ID. */
export async function fetchAgent(id: string): Promise<Agent> {
  return apiFetch<Agent>(`/agents/${id}`);
}
