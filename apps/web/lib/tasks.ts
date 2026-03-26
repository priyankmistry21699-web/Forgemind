import { apiFetch } from "@/lib/api";
import type { Task, TaskList } from "@/types/task";

/** Fetch all tasks for a given run. */
export async function fetchTasksByRun(runId: string): Promise<TaskList> {
  return apiFetch<TaskList>(`/runs/${runId}/tasks`);
}

/** Retry a FAILED task — resets to READY for re-execution. */
export async function retryTask(taskId: string): Promise<Task> {
  return apiFetch<Task>(`/tasks/${taskId}/retry`, { method: "POST" });
}

/** Cancel a READY or RUNNING task. */
export async function cancelTask(taskId: string): Promise<Task> {
  return apiFetch<Task>(`/tasks/${taskId}/cancel`, { method: "POST" });
}
