import { apiFetch } from "@/lib/api";
import type { ExecutionTrace, ReplaySnapshotList, ReplaySnapshot } from "@/types/replay";

/** Fetch full execution trace for a run. */
export async function fetchExecutionTrace(runId: string): Promise<ExecutionTrace> {
  return apiFetch<ExecutionTrace>(`/runs/${runId}/trace`);
}

/** Fetch replay snapshots for a specific task. */
export async function fetchTaskSnapshots(
  taskId: string,
  offset = 0,
  limit = 50,
): Promise<ReplaySnapshotList> {
  return apiFetch<ReplaySnapshotList>(
    `/tasks/${taskId}/snapshots?offset=${offset}&limit=${limit}`,
  );
}

/** Fetch a single replay snapshot by ID. */
export async function fetchSnapshot(snapshotId: string): Promise<ReplaySnapshot> {
  return apiFetch<ReplaySnapshot>(`/replay/snapshots/${snapshotId}`);
}
