import { apiFetch } from "@/lib/api";
import type { ApprovalList, Approval } from "@/types/approval";

/** Fetch approvals, optionally filtered by project/run/status. */
export async function fetchApprovals(opts?: {
  projectId?: string;
  runId?: string;
  status?: string;
}): Promise<ApprovalList> {
  const params = new URLSearchParams();
  if (opts?.projectId) params.set("project_id", opts.projectId);
  if (opts?.runId) params.set("run_id", opts.runId);
  if (opts?.status) params.set("status", opts.status);
  const qs = params.toString();
  return apiFetch<ApprovalList>(`/approvals${qs ? `?${qs}` : ""}`);
}

/** Approve or reject an approval request. */
export async function decideApproval(
  approvalId: string,
  decision: {
    status: "approved" | "rejected";
    decided_by?: string;
    decision_comment?: string;
  },
): Promise<Approval> {
  return apiFetch<Approval>(`/approvals/${approvalId}/decide`, {
    method: "POST",
    body: JSON.stringify(decision),
  });
}
