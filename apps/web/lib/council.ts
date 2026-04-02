import { apiFetch } from "@/lib/api";
import type { CouncilSessionList, CouncilSession } from "@/types/council";

/** Fetch paginated council sessions. */
export async function fetchCouncilSessions(
  offset = 0,
  limit = 50,
): Promise<CouncilSessionList> {
  return apiFetch<CouncilSessionList>(`/council/sessions?offset=${offset}&limit=${limit}`);
}

/** Fetch a single council session by ID. */
export async function fetchCouncilSession(sessionId: string): Promise<CouncilSession> {
  return apiFetch<CouncilSession>(`/council/sessions/${sessionId}`);
}
