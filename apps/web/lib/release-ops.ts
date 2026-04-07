import { apiFetch } from "@/lib/api";
import type {
  ReleasePackage,
  ReleasePackageList,
  DeploymentEnvironment,
  EnvironmentList,
  GateResultList,
  GateEvaluation,
  ReadinessReport,
  RollbackReadiness,
  OperationalTimeline,
} from "@/types/release-ops";

// ---------- Release Packages (FM-131) ----------

export async function fetchRunReleasePackages(
  runId: string,
): Promise<ReleasePackageList> {
  return apiFetch<ReleasePackageList>(`/runs/${runId}/release-packages`);
}

export async function fetchProjectReleasePackages(
  projectId: string,
): Promise<ReleasePackageList> {
  return apiFetch<ReleasePackageList>(
    `/projects/${projectId}/release-packages`,
  );
}

export async function fetchReleasePackage(
  packageId: string,
): Promise<ReleasePackage> {
  return apiFetch<ReleasePackage>(`/release-packages/${packageId}`);
}

export async function generateReleasePackage(
  runId: string,
  version?: string,
): Promise<ReleasePackage> {
  const params = version ? `?version=${encodeURIComponent(version)}` : "";
  return apiFetch<ReleasePackage>(
    `/runs/${runId}/release-packages/generate${params}`,
    { method: "POST" },
  );
}

// ---------- Environments (FM-132) ----------

export async function fetchEnvironments(
  projectId: string,
): Promise<EnvironmentList> {
  return apiFetch<EnvironmentList>(`/projects/${projectId}/environments`);
}

export async function fetchEnvironment(
  envId: string,
): Promise<DeploymentEnvironment> {
  return apiFetch<DeploymentEnvironment>(`/environments/${envId}`);
}

// ---------- Readiness (FM-133) ----------

export async function evaluateReadiness(
  packageId: string,
  environmentId: string,
): Promise<ReadinessReport> {
  return apiFetch<ReadinessReport>(
    `/release-packages/${packageId}/readiness/${environmentId}`,
  );
}

// ---------- Gates (FM-134) ----------

export async function evaluateGates(
  packageId: string,
  environmentId?: string,
): Promise<GateEvaluation> {
  const params = environmentId
    ? `?environment_id=${environmentId}`
    : "";
  return apiFetch<GateEvaluation>(
    `/release-packages/${packageId}/gates/evaluate${params}`,
    { method: "POST" },
  );
}

export async function fetchGateResults(
  packageId: string,
): Promise<GateResultList> {
  return apiFetch<GateResultList>(`/release-packages/${packageId}/gates`);
}

// ---------- Rollback (FM-135) ----------

export async function fetchRollbackReadiness(
  packageId: string,
): Promise<RollbackReadiness> {
  return apiFetch<RollbackReadiness>(
    `/release-packages/${packageId}/rollback-readiness`,
  );
}

// ---------- Reports (FM-136) ----------

export async function fetchPostReleaseReport(
  packageId: string,
): Promise<Record<string, unknown>> {
  return apiFetch<Record<string, unknown>>(
    `/release-packages/${packageId}/report`,
  );
}

export async function recordOutcome(
  packageId: string,
  outcome: string,
  notes?: string,
): Promise<Record<string, unknown>> {
  const params = new URLSearchParams({ outcome });
  if (notes) params.set("notes", notes);
  return apiFetch<Record<string, unknown>>(
    `/release-packages/${packageId}/outcome?${params.toString()}`,
    { method: "POST" },
  );
}

// ---------- Timeline (FM-137) ----------

export async function fetchOperationalTimeline(
  runId: string,
): Promise<OperationalTimeline> {
  return apiFetch<OperationalTimeline>(`/runs/${runId}/timeline`);
}
