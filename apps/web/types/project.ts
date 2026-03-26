/** Project types matching the backend ProjectRead schema. */

export type ProjectStatus =
  | "draft"
  | "planning"
  | "active"
  | "paused"
  | "completed"
  | "failed";

export interface Project {
  id: string;
  name: string;
  description: string | null;
  status: ProjectStatus;
  owner_id: string;
  created_at: string;
  updated_at: string;
}

export interface ProjectList {
  items: Project[];
  total: number;
}
