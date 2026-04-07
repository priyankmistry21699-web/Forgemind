// FM-131–137: Release Operations types

export interface ReleasePackage {
  id: string;
  project_id: string;
  run_id: string;
  version: string;
  status: string;
  summary: string | null;
  artifact_manifest: Record<string, unknown> | null;
  changelog: Record<string, unknown> | null;
  confidence_snapshot: Record<string, unknown> | null;
  rollback_metadata: Record<string, unknown> | null;
  target_environment_id: string | null;
  created_by: string | null;
  created_at: string;
  updated_at: string;
}

export interface ReleasePackageList {
  items: ReleasePackage[];
  total: number;
}

export interface DeploymentEnvironment {
  id: string;
  project_id: string;
  name: string;
  tier: string;
  description: string | null;
  config: Record<string, unknown> | null;
  required_gates: Record<string, unknown> | null;
  promotion_target_id: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface EnvironmentList {
  items: DeploymentEnvironment[];
  total: number;
}

export interface GateResult {
  id: string;
  release_package_id: string;
  gate_name: string;
  gate_status: string;
  detail: string | null;
  metadata_: Record<string, unknown> | null;
  evaluated_at: string;
}

export interface GateResultList {
  items: GateResult[];
  total: number;
}

export interface ReadinessCheck {
  check: string;
  passed: boolean;
  detail: string;
  score?: number;
}

export interface ReadinessReport {
  release_package_id: string;
  environment_id: string;
  is_ready: boolean;
  checks: ReadinessCheck[];
  blockers: string[];
  confidence_score: number;
  passed_checks: number;
  total_checks: number;
}

export interface RollbackReadiness {
  release_package_id: string;
  is_rollback_ready: boolean;
  recovery_points: Array<{
    type: string;
    id: string;
    label: string;
    [key: string]: unknown;
  }>;
  recovery_point_count: number;
  strategies: Array<{
    strategy: string;
    description: string;
    available: string;
  }>;
  risk_signals: Array<{
    signal: string;
    level: string;
    detail: string;
  }>;
  risk_level: string;
}

export interface GateEvaluation {
  release_package_id: string;
  total_gates: number;
  passed: number;
  failed: number;
  all_passed: boolean;
  gate_results: Array<{
    gate: string;
    status: string;
    detail: string;
  }>;
  package_status: string;
}

export interface TimelineEntry {
  timestamp: string | null;
  category: string;
  event: string;
  detail: string;
}

export interface OperationalTimeline {
  run_id: string;
  project_id: string;
  run_status: string;
  total_entries: number;
  categories: Record<string, number>;
  timeline: TimelineEntry[];
}
