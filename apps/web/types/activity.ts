/** Activity and presence types matching the backend schemas. */

export type ActivityType =
  | "project_created"
  | "project_updated"
  | "run_started"
  | "run_completed"
  | "run_failed"
  | "task_completed"
  | "artifact_created"
  | "member_added"
  | "member_removed"
  | "approval_requested"
  | "approval_decided"
  | "escalation_triggered"
  | "patch_proposed"
  | "pr_created"
  | "comment";

export interface ActivityFeedEntry {
  id: string;
  actor_id: string;
  activity_type: ActivityType;
  summary: string;
  project_id: string | null;
  workspace_id: string | null;
  resource_type: string | null;
  resource_id: string | null;
  metadata_: Record<string, unknown> | null;
  created_at: string;
}

export interface ActivityFeedList {
  items: ActivityFeedEntry[];
  total: number;
}

export interface Presence {
  id: string;
  user_id: string;
  status: string;
  current_resource_type: string | null;
  current_resource_id: string | null;
  last_seen_at: string;
}

export interface PresenceList {
  items: Presence[];
  total: number;
}

export interface UserContext {
  user_id: string;
  status: string;
  last_seen_at: string | null;
  current_resource_type: string | null;
  workspace_memberships: number;
  project_memberships: number;
}
