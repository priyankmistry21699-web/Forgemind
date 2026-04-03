// Architecture types — mirrors backend Pydantic schemas (FM-081-090)

export type NodeType =
  | "workspace"
  | "project"
  | "repository"
  | "package"
  | "module"
  | "service"
  | "component"
  | "api"
  | "interface"
  | "datastore"
  | "resource"
  | "external_dependency";

export type EdgeType =
  | "depends_on"
  | "calls"
  | "owns"
  | "reads"
  | "writes"
  | "exposes"
  | "imports"
  | "deploys_to"
  | "emits_event_to"
  | "consumes_event_from";

export type SourceType = "inferred" | "declared" | "imported";
export type NodeStatus = "active" | "deprecated" | "removed";
export type DriftSeverity = "low" | "medium" | "high" | "critical";
export type DriftStatus = "open" | "resolved" | "ignored";
export type RuleCategory =
  | "import"
  | "layer"
  | "ownership"
  | "dependency"
  | "boundary";
export type RuleResultStatus = "pass" | "violation";
export type ImpactSeverity = "low" | "medium" | "high" | "critical";

export interface ArchitectureNode {
  id: string;
  workspace_id: string | null;
  project_id: string;
  repo_id: string | null;
  node_type: NodeType;
  key: string;
  name: string;
  path: string | null;
  language: string | null;
  metadata_: Record<string, unknown> | null;
  source_type: SourceType;
  status: NodeStatus;
  created_at: string;
  updated_at: string;
}

export interface ArchitectureNodeList {
  items: ArchitectureNode[];
  total: number;
}

export interface ArchitectureEdge {
  id: string;
  workspace_id: string | null;
  project_id: string;
  from_node_id: string;
  to_node_id: string;
  edge_type: EdgeType;
  confidence_score: number;
  metadata_: Record<string, unknown> | null;
  source_type: SourceType;
  created_at: string;
}

export interface ArchitectureEdgeList {
  items: ArchitectureEdge[];
  total: number;
}

export interface ArchitectureGraph {
  project_id: string;
  nodes: ArchitectureNode[];
  edges: ArchitectureEdge[];
  node_count: number;
  edge_count: number;
}

export interface ArchitectureSnapshot {
  id: string;
  workspace_id: string | null;
  project_id: string;
  name: string;
  source: string | null;
  summary: Record<string, unknown> | null;
  node_count: number;
  edge_count: number;
  generated_at: string;
}

export interface ArchitectureSnapshotList {
  items: ArchitectureSnapshot[];
  total: number;
}

export interface TopologySummary {
  project_id: string;
  components_found: number;
  edges_found: number;
  layers: string[];
  isolated_nodes: string[];
  high_centrality_nodes: string[];
}

export interface ArchitectureDrift {
  id: string;
  project_id: string;
  drift_type: string;
  severity: DriftSeverity;
  title: string;
  description: string;
  source_snapshot_id: string | null;
  comparison_target: string | null;
  status: DriftStatus;
  metadata_: Record<string, unknown> | null;
  detected_at: string;
  resolved_at: string | null;
}

export interface ArchitectureDriftList {
  items: ArchitectureDrift[];
  total: number;
}

export interface ArchitectureRule {
  id: string;
  project_id: string | null;
  name: string;
  description: string | null;
  category: RuleCategory;
  rule_config: Record<string, unknown>;
  enabled: boolean;
  severity: DriftSeverity;
  created_at: string;
  updated_at: string;
}

export interface ArchitectureRuleList {
  items: ArchitectureRule[];
  total: number;
}

export interface ArchitectureRuleResult {
  id: string;
  rule_id: string;
  project_id: string;
  status: RuleResultStatus;
  message: string;
  details: Record<string, unknown> | null;
  violating_node_ids: string[] | null;
  violating_edge_ids: string[] | null;
  evaluated_at: string;
}

export interface ArchitectureRuleResultList {
  items: ArchitectureRuleResult[];
  total: number;
}

export interface DesignDoc {
  project_id: string;
  title: string;
  content: string;
  sections: string[];
  generated_at: string;
}

export interface ChangeImpactAssessment {
  id: string;
  project_id: string;
  target_node_id: string | null;
  target_path: string | null;
  target_key: string | null;
  severity: ImpactSeverity;
  blast_radius: number;
  impacted_nodes: string[] | null;
  impacted_services: string[] | null;
  rationale: string;
  confidence_score: number;
  metadata_: Record<string, unknown> | null;
  created_at: string;
}

export interface RefactorRecommendation {
  recommendation_type: string;
  title: string;
  description: string;
  severity: DriftSeverity;
  confidence: number;
  affected_nodes: string[];
  rationale: string;
}

export interface RefactorRecommendationList {
  items: RefactorRecommendation[];
  total: number;
}

export interface HealthScoreDetails {
  total_nodes: number;
  total_edges: number;
  declared_nodes: number;
  open_drifts: number;
  total_rule_evaluations: number;
  rule_violations: number;
  isolated_nodes: number;
}

export interface StructuralHealthScore {
  project_id: string;
  overall_score: number;
  component_coverage: number;
  drift_penalty: number;
  rule_compliance: number;
  isolation_ratio: number;
  details: HealthScoreDetails;
}
