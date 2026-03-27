"use client";

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
    rejected: { bg: "bg-red-900/50", text: "text-red-300", dot: "bg-red-400" },
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

interface ApprovalListSectionProps {
  approvals: Approval[];
}

export function ApprovalListSection({ approvals }: ApprovalListSectionProps) {
  if (approvals.length === 0) {
    return (
      <div className="rounded-xl border border-dashed border-[var(--color-border-subtle)] bg-[var(--color-bg-card)]/50 py-10 text-center">
        <div className="mb-3 text-2xl">\u2705</div>
        <p className="text-sm font-medium">No approval requests</p>
        <p className="mt-1 text-xs text-[var(--color-text-muted)]">
          All caught up!
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {approvals.map((approval) => (
        <div
          key={approval.id}
          className={`rounded-lg border p-4 ${
            approval.status === "pending"
              ? "border-amber-800/50 bg-amber-950/20"
              : "border-[var(--color-border)] bg-[var(--color-bg-card)]"
          }`}
        >
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2">
                <h4 className="truncate text-sm font-medium">
                  {approval.title}
                </h4>
                <ApprovalStatusBadge status={approval.status} />
              </div>
              {approval.description && (
                <p className="mt-1 text-xs text-[var(--color-text-muted)]">
                  {approval.description}
                </p>
              )}
              <p className="mt-1 text-xs text-[var(--color-text-muted)]">
                Created {new Date(approval.created_at).toLocaleString()}
                {approval.decided_at &&
                  ` · Decided ${new Date(approval.decided_at).toLocaleString()}`}
                {approval.decided_by && ` by ${approval.decided_by}`}
              </p>
            </div>
          </div>
          {approval.decision_comment && (
            <p className="mt-2 rounded-md bg-[var(--color-bg-secondary)] px-3 py-2 text-xs text-[var(--color-text-muted)]">
              {approval.decision_comment}
            </p>
          )}
        </div>
      ))}
    </div>
  );
}
