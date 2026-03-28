/** Project member types matching the backend schemas. */

export type ProjectRole = "lead" | "contributor" | "reviewer" | "viewer";

export interface ProjectMember {
  id: string;
  project_id: string;
  user_id: string;
  role: ProjectRole;
  created_at: string;
}

export interface ProjectMemberList {
  items: ProjectMember[];
  total: number;
}
