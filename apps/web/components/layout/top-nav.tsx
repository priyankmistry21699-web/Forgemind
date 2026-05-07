"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const PAGE_TITLES: Record<string, string> = {
  "/dashboard": "Dashboard",
  "/dashboard/workspaces": "Workspaces",
  "/dashboard/analytics": "Analytics",
  "/dashboard/agents": "Agents",
  "/dashboard/activity": "Activity",
  "/dashboard/releases": "Releases",
  "/dashboard/replay": "Replay",
  "/dashboard/approvals": "Approvals",
  "/dashboard/trust": "Trust",
  "/dashboard/governance": "Governance",
  "/dashboard/council": "Council",
  "/dashboard/escalations": "Escalations",
  "/dashboard/architecture": "Architecture",
  "/dashboard/knowledge": "Knowledge",
  "/dashboard/costs": "Costs",
  "/dashboard/vault": "Vault",
  "/dashboard/audit": "Audit",
  "/dashboard/connectors": "Connectors",
  "/dashboard/notifications": "Notifications",
  "/dashboard/settings": "Settings",
};

function usePageTitle(): string {
  const pathname = usePathname() ?? "";
  // Exact match first; then longest prefix match for nested routes
  if (PAGE_TITLES[pathname]) return PAGE_TITLES[pathname];
  const match = Object.keys(PAGE_TITLES)
    .filter((k) => k !== "/dashboard" && pathname.startsWith(k))
    .sort((a, b) => b.length - a.length)[0];
  return match ? PAGE_TITLES[match] : "Dashboard";
}

export function TopNav() {
  const title = usePageTitle();

  return (
    <header className="flex h-14 shrink-0 items-center justify-between border-b border-[var(--color-border)] bg-[var(--color-bg-secondary)]/80 backdrop-blur-sm px-6">
      <div className="flex items-center gap-3">
        <h2 className="text-sm font-semibold text-[var(--color-text)]">
          {title}
        </h2>
        <span className="hidden sm:inline-flex items-center rounded-full bg-[var(--color-success-dim)] px-2 py-0.5 text-[10px] font-medium text-[var(--color-success)]">
          <span className="mr-1 inline-block h-1.5 w-1.5 rounded-full bg-[var(--color-success)] animate-pulse" />
          Online
        </span>
      </div>

      <div className="flex items-center gap-2">
        <Link
          href="/dashboard/notifications"
          className="relative flex h-8 w-8 items-center justify-center rounded-lg text-[var(--color-text-muted)] transition-colors hover:bg-[var(--color-bg-card)] hover:text-[var(--color-text)]"
          title="Notifications"
        >
          <svg
            width="15"
            height="15"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
            <path d="M13.73 21a2 2 0 0 1-3.46 0" />
          </svg>
        </Link>
        <Link
          href="/dashboard/settings"
          className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-[var(--color-accent)] to-[var(--color-accent-hover)] text-xs font-bold text-white shadow-sm transition-opacity hover:opacity-90"
          title="Settings"
        >
          U
        </Link>
      </div>
    </header>
  );
}
