import { apiFetch } from "@/lib/api";
import type {
  ActivityFeedList,
  Presence,
  PresenceList,
  UserContext,
} from "@/types/activity";

/** Fetch global activity feed. */
export async function fetchActivity(
  offset = 0,
  limit = 50,
  workspaceId?: string,
): Promise<ActivityFeedList> {
  const params = new URLSearchParams({ offset: String(offset), limit: String(limit) });
  if (workspaceId) params.set("workspace_id", workspaceId);
  return apiFetch<ActivityFeedList>(`/activity?${params}`);
}

/** Fetch workspace-scoped activity. */
export async function fetchWorkspaceActivity(
  workspaceId: string,
  offset = 0,
  limit = 50,
): Promise<ActivityFeedList> {
  return apiFetch<ActivityFeedList>(
    `/workspaces/${workspaceId}/activity?offset=${offset}&limit=${limit}`,
  );
}

/** Update current user's presence. */
export async function updatePresence(data: {
  status?: string;
  current_resource_type?: string | null;
  current_resource_id?: string | null;
}): Promise<Presence> {
  return apiFetch<Presence>("/presence", {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

/** Fetch all online presences. */
export async function fetchPresences(
  offset = 0,
  limit = 100,
): Promise<PresenceList> {
  return apiFetch<PresenceList>(`/presence?offset=${offset}&limit=${limit}`);
}

/** Fetch a specific user's presence. */
export async function fetchUserPresence(userId: string): Promise<Presence> {
  return apiFetch<Presence>(`/presence/${userId}`);
}

/** Fetch user assignment context. */
export async function fetchUserContext(userId: string): Promise<UserContext> {
  return apiFetch<UserContext>(`/users/${userId}/context`);
}
