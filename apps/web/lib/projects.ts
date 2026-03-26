import { apiFetch } from "@/lib/api";
import type { Project, ProjectList } from "@/types/project";
import type { Run } from "@/types/run";

/** Fetch paginated project list from the backend. */
export async function fetchProjects(
  skip = 0,
  limit = 20,
): Promise<ProjectList> {
  return apiFetch<ProjectList>(`/projects?skip=${skip}&limit=${limit}`);
}

/** Fetch a single project by ID. */
export async function fetchProject(projectId: string): Promise<Project> {
  return apiFetch<Project>(`/projects/${projectId}`);
}

/** Fetch the latest run for a project. Returns null if no runs exist. */
export async function fetchLatestRun(projectId: string): Promise<Run | null> {
  try {
    return await apiFetch<Run>(`/projects/${projectId}/runs/latest`);
  } catch {
    return null;
  }
}

/** Create a new project. */
export async function createProject(data: {
  name: string;
  description?: string | null;
}): Promise<Project> {
  return apiFetch<Project>("/projects", {
    method: "POST",
    body: JSON.stringify(data),
  });
}
