import { apiFetch } from "@/lib/api";
import type { ConnectorList, ProjectReadinessSummary } from "@/types/connector";

/** Fetch all registered connectors. */
export async function fetchConnectors(): Promise<ConnectorList> {
  return apiFetch<ConnectorList>("/connectors");
}

/** Fetch readiness summary for a project's connectors. */
export async function fetchProjectReadiness(
  projectId: string,
): Promise<ProjectReadinessSummary> {
  return apiFetch<ProjectReadinessSummary>(
    `/projects/${projectId}/connectors/readiness`,
  );
}
