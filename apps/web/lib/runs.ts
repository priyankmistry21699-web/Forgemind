import { apiFetch } from "@/lib/api";
import type { Run, RunList } from "@/types/run";

/** Fetch a single run by ID. */
export async function fetchRun(runId: string): Promise<Run> {
  return apiFetch<Run>(`/runs/${runId}`);
}

/** Fetch all runs for a project. */
export async function fetchRunsByProject(
  projectId: string,
  skip = 0,
  limit = 20,
): Promise<RunList> {
  return apiFetch<RunList>(
    `/projects/${projectId}/runs?skip=${skip}&limit=${limit}`,
  );
}
