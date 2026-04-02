"use client";

import Link from "next/link";

export default function SettingsPage() {
  return (
    <div className="space-y-6">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-xs text-[var(--color-text-muted)]">
        <Link href="/dashboard" className="hover:text-[var(--color-text)] transition-colors">
          Dashboard
        </Link>
        <span>/</span>
        <span className="text-[var(--color-text)]">Settings</span>
      </div>

      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Settings</h1>
        <p className="mt-1 text-sm text-[var(--color-text-muted)]">
          Platform configuration and preferences
        </p>
      </div>

      {/* Placeholder sections */}
      <div className="space-y-4">
        <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-bg-card)] p-6">
          <h2 className="text-sm font-semibold text-[var(--color-text)]">General</h2>
          <p className="mt-1 text-xs text-[var(--color-text-muted)]">
            Platform name, default project settings, and global configuration.
          </p>
          <div className="mt-4 rounded-lg border border-dashed border-[var(--color-border)] p-8 text-center">
            <p className="text-xs text-[var(--color-text-dim)]">
              Settings will be available after authentication is implemented (FM-074).
            </p>
          </div>
        </div>

        <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-bg-card)] p-6">
          <h2 className="text-sm font-semibold text-[var(--color-text)]">Authentication</h2>
          <p className="mt-1 text-xs text-[var(--color-text-muted)]">
            Login provider, session duration, and identity configuration.
          </p>
          <div className="mt-4 rounded-lg border border-dashed border-[var(--color-border)] p-8 text-center">
            <p className="text-xs text-[var(--color-text-dim)]">
              Requires FM-074 (Real Authentication Integration).
            </p>
          </div>
        </div>

        <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-bg-card)] p-6">
          <h2 className="text-sm font-semibold text-[var(--color-text)]">Notifications</h2>
          <p className="mt-1 text-xs text-[var(--color-text-muted)]">
            Alert thresholds, webhook destinations, and notification preferences.
          </p>
          <div className="mt-4 rounded-lg border border-dashed border-[var(--color-border)] p-8 text-center">
            <p className="text-xs text-[var(--color-text-dim)]">
              Requires FM-077 (Real-Time UX Integration).
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
