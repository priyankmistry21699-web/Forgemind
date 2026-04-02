/** Agent types matching the backend schemas. */

export type AgentStatus = "active" | "inactive" | "deprecated";

export interface Agent {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  status: AgentStatus;
  capabilities: string[] | null;
  supported_task_types: string[] | null;
  created_at: string;
  updated_at: string;
}

export interface AgentList {
  items: Agent[];
  total: number;
}
