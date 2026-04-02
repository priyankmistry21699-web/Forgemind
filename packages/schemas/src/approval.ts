/** Approval types matching the backend ApprovalRead schema. */

export type ApprovalStatus = "pending" | "approved" | "rejected";

export interface Approval {
  id: string;
  status: ApprovalStatus;
  title: string;
  description: string | null;
  project_id: string;
  run_id: string | null;
  task_id: string | null;
  artifact_id: string | null;
  decided_by: string | null;
  decision_comment: string | null;
  decided_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface ApprovalList {
  items: Approval[];
  total: number;
}
