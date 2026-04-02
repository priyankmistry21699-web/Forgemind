/** Connector types matching the backend schemas (FM-041). */

export type ConnectorStatus = "available" | "configured" | "unavailable";
export type ConnectorReadiness = "missing" | "configured" | "blocked" | "ready";
export type ConnectorPriority = "required" | "recommended" | "optional";

export interface Connector {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  connector_type: string;
  status: ConnectorStatus;
  capabilities: string[] | null;
  created_at: string;
  updated_at: string;
}

export interface ConnectorList {
  items: Connector[];
  total: number;
}

export interface ProjectConnectorLink {
  id: string;
  project_id: string;
  connector_id: string;
  connector_slug: string;
  connector_name: string;
  priority: ConnectorPriority;
  readiness: ConnectorReadiness;
  config_snapshot: Record<string, unknown> | null;
  blocker_reason: string | null;
  created_at: string;
  updated_at: string;
}

export interface ProjectReadinessSummary {
  links: ProjectConnectorLink[];
  total: number;
  ready_count: number;
  configured_count: number;
  blocked_count: number;
  missing_count: number;
  all_required_ready: boolean;
}
