"use client";

import { useState } from "react";
import { decideApproval } from "@/lib/approvals";
import type { Approval } from "@/types/approval";

const STATUS_STYLES: Record<string, { bg: string; text: string; dot: string }> =
  {
    pending: {
      bg: "bg-amber-900/50",
      text: "text-amber-300",
      dot: "bg-amber-400",
    },
    approved: {
      bg: "bg-green-900/50",
      text: "text-green-300",
      dot: "bg-green-400",
    },
    rejected: {
      bg: "bg-red-900/50",
      text: "text-red-300",
      dot: "bg-red-400",
    },
  };

function ApprovalStatusBadge({ status }: { status: string }) {
  const style = STATUS_STYLES[status] ?? STATUS_STYLES.pending;
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-[11px] font-medium uppercase tracking-wide ${style.bg} ${style.text}`}
    >
      <span className={`inline-block h-1.5 w-1.5 rounded-full ${style.dot}`} />
      {status}
    </span>
  );
}

interface ApprovalCardProps {
  approval: Approval;
  onDecided: () => void;
}

export function ApprovalCard({ approval, onDecided }: ApprovalCardProps) {
  const [comment, setComment] = useState("");
  const [deciding, setDeciding] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isPending = approval.status === "pending";

  async function handleDecide(decision: "approved" | "rejected") {
    setDeciding(true);
    setError(null);
    try {
      await decideApproval(approval.id, {
        status: decision,
        decided_by: "user",
        decision_comment: comment || undefined,
      });
      onDecided();
    } catch (err: unknown) {
      setError(
        err instanceof Error ? err.message : "Failed to submit decision",
      );
    } finally {
      setDeciding(false);
    }
  }

  return (
    <div
      className={`rounded-xl border p-5 transition-all ${
        isPending
          ? "border-amber-800/50 bg-amber-950/20"
          : "border-[var(--color-border)] bg-[var(--color-bg-card)]"
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <h3 className="truncate text-sm font-medium">{approval.title}</h3>
            <ApprovalStatusBadge status={approval.status} />
          </div>
          {approval.description && (
            <p className="mt-1 text-xs text-[var(--color-text-muted)]">
              {approval.description}
            </p>
          )}
          <p className="mt-1 text-[11px] text-[var(--color-text-muted)]">
            Created {new Date(approval.created_at).toLocaleString()}
            {approval.run_id && ` · Run ${approval.run_id.slice(0, 8)}...`}
          </p>
        </div>
      </div>

      {/* Decision details (for resolved approvals) */}
      {!isPending && approval.decided_at && (
        <div className="mt-3 rounded-md bg-[var(--color-bg-secondary)] px-3 py-2">
          <p className="text-xs text-[var(--color-text-muted)]">
            {approval.status === "approved" ? "Approved" : "Rejected"}
            {approval.decided_by && ` by ${approval.decided_by}`} on{" "}
            {new Date(approval.decided_at).toLocaleString()}
          </p>
          {approval.decision_comment && (
            <p className="mt-1 text-xs">{approval.decision_comment}</p>
          )}
        </div>
      )}

      {/* Decision actions (for pending approvals) */}
      {isPending && (
        <div className="mt-3 space-y-2">
          <textarea
            placeholder="Optional comment..."
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            rows={2}
            className="w-full rounded-md border border-[var(--color-border)] bg-[var(--color-bg-secondary)] px-3 py-2 text-xs text-[var(--color-text)] placeholder:text-[var(--color-text-muted)] focus:border-[var(--color-accent)] focus:outline-none"
          />
          <div className="flex gap-2">
            <button
              onClick={() => handleDecide("approved")}
              disabled={deciding}
              className="rounded-lg bg-green-700 px-4 py-2 text-xs font-medium text-white shadow-sm transition-all hover:bg-green-600 hover:-translate-y-0.5 disabled:opacity-50"
            >
              {deciding ? "..." : "\u2713 Approve"}
            </button>
            <button
              onClick={() => handleDecide("rejected")}
              disabled={deciding}
              className="rounded-lg bg-red-700 px-4 py-2 text-xs font-medium text-white shadow-sm transition-all hover:bg-red-600 hover:-translate-y-0.5 disabled:opacity-50"
            >
              {deciding ? "..." : "\u2717 Reject"}
            </button>
          </div>
          {error && <p className="text-xs text-red-400">{error}</p>}
        </div>
      )}
    </div>
  );
}
