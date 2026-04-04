import { apiFetch } from "@/lib/api";
import type { Constitution } from "@/types/constitution";

/** Fetch the constitution for a project. Returns null if none exists. */
export async function fetchConstitution(
  projectId: string,
): Promise<Constitution | null> {
  try {
    return await apiFetch<Constitution>(`/projects/${projectId}/constitution`);
  } catch {
    return null;
  }
}

/** Create or replace the constitution for a project. */
export async function saveConstitution(
  projectId: string,
  data: { content: string; title?: string; summary?: string },
): Promise<Constitution> {
  return apiFetch<Constitution>(`/projects/${projectId}/constitution`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

/** Delete the constitution for a project. */
export async function deleteConstitution(projectId: string): Promise<void> {
  await apiFetch(`/projects/${projectId}/constitution`, {
    method: "DELETE",
  });
}
