import { apiFetch } from "@/lib/api";
import type { Workspace, WorkspaceList, WorkspaceMemberList } from "@/types/workspace";

/** Fetch paginated workspace list. */
export async function fetchWorkspaces(
  offset = 0,
  limit = 50,
): Promise<WorkspaceList> {
  return apiFetch<WorkspaceList>(`/workspaces?offset=${offset}&limit=${limit}`);
}

/** Fetch a single workspace by ID. */
export async function fetchWorkspace(workspaceId: string): Promise<Workspace> {
  return apiFetch<Workspace>(`/workspaces/${workspaceId}`);
}

/** Create a new workspace. */
export async function createWorkspace(data: {
  name: string;
  slug: string;
  description?: string | null;
}): Promise<Workspace> {
  return apiFetch<Workspace>("/workspaces", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/** Update a workspace. */
export async function updateWorkspace(
  workspaceId: string,
  data: { name?: string; description?: string | null },
): Promise<Workspace> {
  return apiFetch<Workspace>(`/workspaces/${workspaceId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

/** Fetch members of a workspace. */
export async function fetchWorkspaceMembers(
  workspaceId: string,
  offset = 0,
  limit = 50,
): Promise<WorkspaceMemberList> {
  return apiFetch<WorkspaceMemberList>(
    `/workspaces/${workspaceId}/members?offset=${offset}&limit=${limit}`,
  );
}

/** Add a member to a workspace. */
export async function addWorkspaceMember(
  workspaceId: string,
  data: { user_id: string; role: string },
): Promise<void> {
  await apiFetch(`/workspaces/${workspaceId}/members`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}
