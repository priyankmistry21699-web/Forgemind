import { apiFetch } from "@/lib/api";
import type { Artifact, ArtifactList } from "@/types/artifact";

/** Fetch artifacts for a project, optionally filtered by run. */
export async function fetchArtifacts(
  projectId: string,
  runId?: string,
): Promise<ArtifactList> {
  const params = new URLSearchParams();
  if (runId) params.set("run_id", runId);
  const qs = params.toString();
  return apiFetch<ArtifactList>(
    `/projects/${projectId}/artifacts${qs ? `?${qs}` : ""}`,
  );
}

/** Fetch a single artifact by ID. */
export async function fetchArtifact(artifactId: string): Promise<Artifact> {
  return apiFetch<Artifact>(`/artifacts/${artifactId}`);
}
