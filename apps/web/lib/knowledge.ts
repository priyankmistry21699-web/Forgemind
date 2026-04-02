import { apiFetch } from "@/lib/api";
import type { ProjectKnowledgeList, ProjectKnowledge } from "@/types/knowledge";

/** Fetch paginated knowledge entries for a project. */
export async function fetchProjectKnowledge(
  projectId: string,
  offset = 0,
  limit = 50,
): Promise<ProjectKnowledgeList> {
  return apiFetch<ProjectKnowledgeList>(
    `/projects/${projectId}/knowledge?offset=${offset}&limit=${limit}`,
  );
}

/** Fetch a single knowledge entry by ID. */
export async function fetchKnowledgeEntry(id: string): Promise<ProjectKnowledge> {
  return apiFetch<ProjectKnowledge>(`/knowledge/${id}`);
}
