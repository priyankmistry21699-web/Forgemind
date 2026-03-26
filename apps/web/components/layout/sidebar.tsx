"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_ITEMS = [
  { label: "Dashboard", href: "/dashboard" },
  { label: "Approvals", href: "/dashboard/approvals" },
  { label: "Agents", href: "/agents", disabled: true },
  { label: "Connectors", href: "/connectors", disabled: true },
  { label: "Settings", href: "/settings", disabled: true },
];

/** Active-link items that are NOT the Dashboard catch-all. */
const CHILD_ROUTES = NAV_ITEMS.filter(
  (i) => !i.disabled && i.href !== "/dashboard",
).map((i) => i.href);

export function Sidebar() {
  const pathname = usePathname();

  const isItemActive = (href: string) => {
    if (href === "/dashboard") {
      // Dashboard is active on exact match OR any /dashboard/* child that
      // doesn't match a more-specific sidebar item (e.g. Approvals).
      return (
        pathname === "/dashboard" ||
        (pathname?.startsWith("/dashboard/") &&
          !CHILD_ROUTES.some((r) => pathname?.startsWith(r)))
      );
    }
    return pathname === href || !!pathname?.startsWith(href);
  };

  return (
    <aside className="flex w-56 shrink-0 flex-col border-r border-[var(--color-border)] bg-[var(--color-bg-secondary)]">
      {/* Brand */}
      <div className="flex h-14 items-center gap-2 border-b border-[var(--color-border)] px-4">
        <div className="flex h-7 w-7 items-center justify-center rounded-md bg-[var(--color-accent)] text-xs font-bold text-white">
          FM
        </div>
        <span className="text-sm font-semibold tracking-tight">ForgeMind</span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 px-2 py-3">
        {NAV_ITEMS.map((item) => {
          const active = isItemActive(item.href);

          return item.disabled ? (
            <span
              key={item.href}
              className="flex items-center rounded-md px-3 py-2 text-sm text-[var(--color-text-muted)] opacity-50 cursor-not-allowed"
            >
              {item.label}
              <span className="ml-auto text-[10px] uppercase tracking-wide opacity-60">
                soon
              </span>
            </span>
          ) : (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center rounded-md px-3 py-2 text-sm transition-colors ${
                active
                  ? "bg-[var(--color-bg-card)] text-[var(--color-text)] font-medium"
                  : "text-[var(--color-text-muted)] hover:bg-[var(--color-bg-card)] hover:text-[var(--color-text)]"
              }`}
            >
              {item.label}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="border-t border-[var(--color-border)] px-4 py-3">
        <p className="text-[11px] text-[var(--color-text-muted)]">
          ForgeMind v0.3.0
        </p>
      </div>
    </aside>
  );
}
