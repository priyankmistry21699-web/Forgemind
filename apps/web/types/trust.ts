/** Trust scoring types matching the backend schemas (FM-046/FM-050). */

export type RiskLevel = "low" | "medium" | "high" | "critical";
export type EntityType = "task" | "artifact" | "run";

export interface TrustScore {
  id: string;
  entity_type: EntityType;
  entity_id: string;
  trust_score: number;
  confidence: number;
  risk_level: RiskLevel;
  factors: Record<string, unknown> | null;
  project_id: string | null;
  run_id: string | null;
  assessed_at: string;
}

export interface TrustScoreList {
  items: TrustScore[];
  total: number;
}

export interface RiskSummary {
  run_id: string;
  overall_risk: RiskLevel;
  total_assessments: number;
  risk_breakdown: Record<string, number>;
  high_risk_tasks: string[];
}
