import { apiFetch } from "@/lib/api";
import type { ProjectMember, ProjectMemberList } from "@/types/project-member";

/** Fetch project members. */
export async function fetchProjectMembers(
  projectId: string,
  offset = 0,
  limit = 50,
): Promise<ProjectMemberList> {
  return apiFetch<ProjectMemberList>(
    `/projects/${projectId}/members?offset=${offset}&limit=${limit}`,
  );
}

/** Add a member to a project. */
export async function addProjectMember(
  projectId: string,
  data: { user_id: string; role: string },
): Promise<ProjectMember> {
  return apiFetch<ProjectMember>(`/projects/${projectId}/members`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/** Remove a project member. */
export async function removeProjectMember(memberId: string): Promise<void> {
  await apiFetch(`/members/${memberId}`, { method: "DELETE" });
}
