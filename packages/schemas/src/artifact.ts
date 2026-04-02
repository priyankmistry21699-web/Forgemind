/** Artifact types matching the backend ArtifactRead schema. */

export type ArtifactType =
  | "plan_summary"
  | "architecture"
  | "implementation"
  | "review"
  | "test_report"
  | "documentation"
  | "other";

export interface Artifact {
  id: string;
  title: string;
  artifact_type: ArtifactType;
  content: string | null;
  meta: Record<string, unknown> | null;
  version: number;
  project_id: string;
  run_id: string | null;
  task_id: string | null;
  created_by: string | null;
  created_at: string;
  updated_at: string;
}

export interface ArtifactList {
  items: Artifact[];
  total: number;
}
