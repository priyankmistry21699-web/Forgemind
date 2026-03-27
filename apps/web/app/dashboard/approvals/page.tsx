"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { fetchApprovals } from "@/lib/approvals";
import type { Approval } from "@/types/approval";
import { ApprovalCard } from "@/components/approvals/approval-card";

export default function ApprovalsPage() {
  const [approvals, setApprovals] = useState<Approval[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<"all" | "pending" | "resolved">("all");

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchApprovals(
        filter === "pending"
          ? { status: "pending" }
          : filter === "resolved"
            ? undefined
            : undefined,
      );
      let items = data.items;
      if (filter === "resolved") {
        items = items.filter((a) => a.status !== "pending");
      }
      setApprovals(items);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load approvals");
    } finally {
      setLoading(false);
    }
  }, [filter]);

  useEffect(() => {
    load();
  }, [load]);

  const pendingCount = approvals.filter((a) => a.status === "pending").length;

  return (
    <div className="space-y-6">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-xs text-[var(--color-text-muted)]">
        <Link
          href="/dashboard"
          className="hover:text-[var(--color-text)] transition-colors"
        >
          Dashboard
        </Link>
        <span>/</span>
        <span className="text-[var(--color-text)]">Approvals</span>
      </div>

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Approvals</h1>
          <p className="mt-1 text-sm text-[var(--color-text-muted)]">
            Review and decide on pending approval requests
          </p>
        </div>
        {pendingCount > 0 && (
          <span className="rounded-full bg-amber-900/50 px-3 py-1 text-xs font-medium text-amber-300">
            {pendingCount} pending
          </span>
        )}
      </div>

      {/* Filter tabs */}
      <div className="flex gap-1 rounded-xl bg-[var(--color-bg-secondary)] p-1">
        {(["all", "pending", "resolved"] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setFilter(tab)}
            className={`rounded-lg px-4 py-2 text-xs font-medium capitalize transition-all ${
              filter === tab
                ? "bg-[var(--color-bg-card)] text-[var(--color-text)] shadow-sm"
                : "text-[var(--color-text-muted)] hover:text-[var(--color-text)]"
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Content */}
      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="animate-pulse rounded-lg border border-[var(--color-border)] bg-[var(--color-bg-card)] p-4"
            >
              <div className="h-4 w-1/3 rounded bg-[var(--color-bg-secondary)]" />
              <div className="mt-2 h-3 w-2/3 rounded bg-[var(--color-bg-secondary)]" />
            </div>
          ))}
        </div>
      ) : error ? (
        <div className="rounded-lg border border-red-900/50 bg-red-950/20 p-4">
          <p className="text-sm font-medium text-red-400">
            Failed to load approvals
          </p>
          <p className="mt-1 text-xs text-red-400/70">{error}</p>
        </div>
      ) : approvals.length === 0 ? (
        <div className="rounded-lg border border-dashed border-[var(--color-border)] py-12 text-center">
          <p className="text-sm text-[var(--color-text-muted)]">
            {filter === "pending"
              ? "No pending approvals"
              : filter === "resolved"
                ? "No resolved approvals yet"
                : "No approval requests yet"}
          </p>
          <p className="mt-1 text-xs text-[var(--color-text-muted)]">
            Approval requests are created automatically when high-impact tasks
            complete.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {approvals.map((approval) => (
            <ApprovalCard
              key={approval.id}
              approval={approval}
              onDecided={load}
            />
          ))}
        </div>
      )}
    </div>
  );
}
