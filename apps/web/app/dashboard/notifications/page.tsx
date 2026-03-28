"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { fetchNotifications, markNotificationRead, markAllRead } from "@/lib/notifications";
import type { Notification } from "@/types/notification";

const PRIORITY_COLORS: Record<string, string> = {
  urgent: "text-red-400 bg-red-500/10 border-red-500/30",
  high: "text-amber-400 bg-amber-500/10 border-amber-500/30",
  normal: "text-blue-400 bg-blue-500/10 border-blue-500/30",
  low: "text-[var(--color-text-dim)] bg-[var(--color-bg-secondary)] border-[var(--color-border)]",
};

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<"all" | "unread">("all");

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchNotifications(filter === "unread");
      setNotifications(data.items);
      setUnreadCount(data.unread_count);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load notifications");
    } finally {
      setLoading(false);
    }
  }, [filter]);

  useEffect(() => {
    load();
  }, [load]);

  const handleMarkRead = async (id: string) => {
    try {
      await markNotificationRead(id);
      load();
    } catch {
      // ignore
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await markAllRead();
      load();
    } catch {
      // ignore
    }
  };

  return (
    <div className="space-y-6">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-xs text-[var(--color-text-muted)]">
        <Link href="/dashboard" className="hover:text-[var(--color-text)] transition-colors">
          Dashboard
        </Link>
        <span>/</span>
        <span className="text-[var(--color-text)]">Notifications</span>
      </div>

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Notifications</h1>
          <p className="mt-1 text-sm text-[var(--color-text-muted)]">
            Stay updated on approvals, runs, and team activity
          </p>
        </div>
        <div className="flex items-center gap-3">
          {unreadCount > 0 && (
            <span className="rounded-full bg-[var(--color-accent)]/20 px-3 py-1 text-xs font-medium text-[var(--color-accent)]">
              {unreadCount} unread
            </span>
          )}
          <button
            onClick={handleMarkAllRead}
            className="rounded-lg border border-[var(--color-border)] px-3 py-1.5 text-xs font-medium text-[var(--color-text-muted)] transition-colors hover:bg-[var(--color-bg-secondary)]"
          >
            Mark all read
          </button>
        </div>
      </div>

      {/* Filter tabs */}
      <div className="flex gap-1 rounded-xl bg-[var(--color-bg-secondary)] p-1">
        {(["all", "unread"] as const).map((tab) => (
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

      {/* Error */}
      {error && (
        <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-400">
          {error}
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="flex items-center justify-center py-12">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-[var(--color-accent)] border-t-transparent" />
        </div>
      )}

      {/* Notification list */}
      {!loading && notifications.length === 0 && (
        <div className="rounded-xl border border-dashed border-[var(--color-border)] p-12 text-center">
          <p className="text-sm text-[var(--color-text-muted)]">No notifications</p>
        </div>
      )}

      {!loading && notifications.length > 0 && (
        <div className="space-y-2">
          {notifications.map((n) => (
            <div
              key={n.id}
              className={`flex items-start gap-4 rounded-xl border p-4 transition-all ${
                n.is_read
                  ? "border-[var(--color-border)] bg-[var(--color-bg-card)]"
                  : "border-[var(--color-accent)]/20 bg-[var(--color-accent-glow)]"
              }`}
            >
              {/* Priority badge */}
              <span
                className={`mt-0.5 shrink-0 rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase ${PRIORITY_COLORS[n.priority] ?? PRIORITY_COLORS.normal}`}
              >
                {n.priority}
              </span>

              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium text-[var(--color-text)]">{n.title}</p>
                {n.body && (
                  <p className="mt-1 text-xs text-[var(--color-text-muted)] line-clamp-2">
                    {n.body}
                  </p>
                )}
                <div className="mt-2 flex items-center gap-3 text-[10px] text-[var(--color-text-dim)]">
                  <span>{n.notification_type.replace(/_/g, " ")}</span>
                  <span>{new Date(n.created_at).toLocaleString()}</span>
                </div>
              </div>

              {!n.is_read && (
                <button
                  onClick={() => handleMarkRead(n.id)}
                  className="shrink-0 rounded-lg border border-[var(--color-border)] px-2 py-1 text-[10px] font-medium text-[var(--color-text-muted)] hover:bg-[var(--color-bg-secondary)]"
                >
                  Mark read
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
