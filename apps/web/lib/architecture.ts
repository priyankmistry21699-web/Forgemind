import { apiFetch } from "@/lib/api";
import type {
  ArchitectureGraph,
  ArchitectureNodeList,
  ArchitectureEdgeList,
  ArchitectureSnapshotList,
  ArchitectureDriftList,
  ArchitectureRuleList,
  ArchitectureRuleResultList,
  DesignDoc,
  ChangeImpactAssessment,
  RefactorRecommendationList,
  StructuralHealthScore,
} from "@/types/architecture";

/** Fetch the full architecture graph for a project. */
export async function fetchArchitectureGraph(
  projectId: string,
): Promise<ArchitectureGraph> {
  return apiFetch<ArchitectureGraph>(
    `/projects/${projectId}/architecture/graph`,
  );
}

/** List architecture nodes. */
export async function fetchArchitectureNodes(
  projectId: string,
  offset = 0,
  limit = 100,
): Promise<ArchitectureNodeList> {
  return apiFetch<ArchitectureNodeList>(
    `/projects/${projectId}/architecture/nodes?offset=${offset}&limit=${limit}`,
  );
}

/** List architecture edges. */
export async function fetchArchitectureEdges(
  projectId: string,
  offset = 0,
  limit = 100,
): Promise<ArchitectureEdgeList> {
  return apiFetch<ArchitectureEdgeList>(
    `/projects/${projectId}/architecture/edges?offset=${offset}&limit=${limit}`,
  );
}

/** List snapshots. */
export async function fetchArchitectureSnapshots(
  projectId: string,
): Promise<ArchitectureSnapshotList> {
  return apiFetch<ArchitectureSnapshotList>(
    `/projects/${projectId}/architecture/snapshots`,
  );
}

/** Trigger topology mapping. */
export async function mapTopology(projectId: string): Promise<unknown> {
  return apiFetch(`/projects/${projectId}/architecture/topology/map`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  });
}

/** Trigger drift detection. */
export async function detectDrift(
  projectId: string,
): Promise<ArchitectureDriftList> {
  return apiFetch<ArchitectureDriftList>(
    `/projects/${projectId}/architecture/drift/detect`,
    { method: "POST" },
  );
}

/** List drift findings. */
export async function fetchDrifts(
  projectId: string,
): Promise<ArchitectureDriftList> {
  return apiFetch<ArchitectureDriftList>(
    `/projects/${projectId}/architecture/drift`,
  );
}

/** List architecture rules. */
export async function fetchArchitectureRules(
  projectId: string,
): Promise<ArchitectureRuleList> {
  return apiFetch<ArchitectureRuleList>(
    `/projects/${projectId}/architecture/rules`,
  );
}

/** List rule evaluation results. */
export async function fetchRuleResults(
  projectId: string,
): Promise<ArchitectureRuleResultList> {
  return apiFetch<ArchitectureRuleResultList>(
    `/projects/${projectId}/architecture/rule-results`,
  );
}

/** Generate a design document. */
export async function generateDesignDoc(projectId: string): Promise<DesignDoc> {
  return apiFetch<DesignDoc>(`/projects/${projectId}/architecture/design-doc`, {
    method: "POST",
  });
}

/** Run impact analysis. */
export async function analyseImpact(
  projectId: string,
  body: { node_id?: string; file_path?: string; module_key?: string },
): Promise<ChangeImpactAssessment> {
  return apiFetch<ChangeImpactAssessment>(
    `/projects/${projectId}/architecture/impact-analysis`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    },
  );
}

/** Fetch refactor recommendations. */
export async function fetchRecommendations(
  projectId: string,
): Promise<RefactorRecommendationList> {
  return apiFetch<RefactorRecommendationList>(
    `/projects/${projectId}/architecture/recommendations`,
  );
}

/** Fetch structural health score. */
export async function fetchHealthScore(
  projectId: string,
): Promise<StructuralHealthScore> {
  return apiFetch<StructuralHealthScore>(
    `/projects/${projectId}/architecture/health-score`,
  );
}
