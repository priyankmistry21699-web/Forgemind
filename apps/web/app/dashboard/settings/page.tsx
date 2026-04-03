"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

interface UserSettings {
  theme: "light" | "dark" | "system";
  itemsPerPage: number;
  dateFormat: "relative" | "absolute";
  notificationSound: boolean;
  emailNotifications: boolean;
  autoRefreshInterval: number;
}

const DEFAULT_SETTINGS: UserSettings = {
  theme: "system",
  itemsPerPage: 25,
  dateFormat: "relative",
  notificationSound: true,
  emailNotifications: true,
  autoRefreshInterval: 30,
};

const STORAGE_KEY = "forgemind_settings";

function loadSettings(): UserSettings {
  if (typeof window === "undefined") return DEFAULT_SETTINGS;
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return DEFAULT_SETTINGS;
    return { ...DEFAULT_SETTINGS, ...JSON.parse(raw) };
  } catch {
    return DEFAULT_SETTINGS;
  }
}

function saveSettings(settings: UserSettings) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
}

export default function SettingsPage() {
  const [settings, setSettings] = useState<UserSettings>(DEFAULT_SETTINGS);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    setSettings(loadSettings());
  }, []);

  function update<K extends keyof UserSettings>(
    key: K,
    value: UserSettings[K],
  ) {
    setSettings((prev) => {
      const next = { ...prev, [key]: value };
      saveSettings(next);
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
      return next;
    });
  }

  function resetDefaults() {
    saveSettings(DEFAULT_SETTINGS);
    setSettings(DEFAULT_SETTINGS);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  }

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
        <span className="text-[var(--color-text)]">Settings</span>
      </div>

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Settings</h1>
          <p className="mt-1 text-sm text-[var(--color-text-muted)]">
            Platform configuration and preferences
          </p>
        </div>
        {saved && (
          <span className="text-xs text-emerald-400 bg-emerald-500/10 px-3 py-1 rounded-full">
            Saved
          </span>
        )}
      </div>

      {/* General */}
      <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-bg-card)] p-6 space-y-5">
        <div>
          <h2 className="text-sm font-semibold text-[var(--color-text)]">
            General
          </h2>
          <p className="mt-1 text-xs text-[var(--color-text-muted)]">
            Theme, display, and dashboard preferences.
          </p>
        </div>

        <div className="grid gap-5 sm:grid-cols-2">
          {/* Theme */}
          <label className="space-y-1.5">
            <span className="block text-xs font-medium text-[var(--color-text-muted)]">
              Theme
            </span>
            <select
              value={settings.theme}
              onChange={(e) =>
                update("theme", e.target.value as UserSettings["theme"])
              }
              className="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-bg-secondary)] px-3 py-2 text-sm text-[var(--color-text)] focus:outline-none focus:ring-1 focus:ring-[var(--color-accent)]"
            >
              <option value="system">System</option>
              <option value="light">Light</option>
              <option value="dark">Dark</option>
            </select>
          </label>

          {/* Items per page */}
          <label className="space-y-1.5">
            <span className="block text-xs font-medium text-[var(--color-text-muted)]">
              Items per page
            </span>
            <select
              value={settings.itemsPerPage}
              onChange={(e) => update("itemsPerPage", Number(e.target.value))}
              className="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-bg-secondary)] px-3 py-2 text-sm text-[var(--color-text)] focus:outline-none focus:ring-1 focus:ring-[var(--color-accent)]"
            >
              <option value={10}>10</option>
              <option value={25}>25</option>
              <option value={50}>50</option>
              <option value={100}>100</option>
            </select>
          </label>

          {/* Date format */}
          <label className="space-y-1.5">
            <span className="block text-xs font-medium text-[var(--color-text-muted)]">
              Date format
            </span>
            <select
              value={settings.dateFormat}
              onChange={(e) =>
                update(
                  "dateFormat",
                  e.target.value as UserSettings["dateFormat"],
                )
              }
              className="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-bg-secondary)] px-3 py-2 text-sm text-[var(--color-text)] focus:outline-none focus:ring-1 focus:ring-[var(--color-accent)]"
            >
              <option value="relative">
                Relative (e.g. &quot;2 hours ago&quot;)
              </option>
              <option value="absolute">
                Absolute (e.g. &quot;2025-01-15 14:30&quot;)
              </option>
            </select>
          </label>

          {/* Auto-refresh */}
          <label className="space-y-1.5">
            <span className="block text-xs font-medium text-[var(--color-text-muted)]">
              Auto-refresh interval
            </span>
            <select
              value={settings.autoRefreshInterval}
              onChange={(e) =>
                update("autoRefreshInterval", Number(e.target.value))
              }
              className="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-bg-secondary)] px-3 py-2 text-sm text-[var(--color-text)] focus:outline-none focus:ring-1 focus:ring-[var(--color-accent)]"
            >
              <option value={0}>Disabled</option>
              <option value={10}>10 seconds</option>
              <option value={30}>30 seconds</option>
              <option value={60}>1 minute</option>
              <option value={300}>5 minutes</option>
            </select>
          </label>
        </div>
      </div>

      {/* Notifications */}
      <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-bg-card)] p-6 space-y-5">
        <div>
          <h2 className="text-sm font-semibold text-[var(--color-text)]">
            Notifications
          </h2>
          <p className="mt-1 text-xs text-[var(--color-text-muted)]">
            Alert preferences and notification delivery.
          </p>
        </div>

        <div className="space-y-4">
          {/* Notification sound */}
          <label className="flex items-center justify-between rounded-lg border border-[var(--color-border)] bg-[var(--color-bg-secondary)] px-4 py-3">
            <div>
              <span className="block text-sm text-[var(--color-text)]">
                Notification sound
              </span>
              <span className="block text-xs text-[var(--color-text-dim)]">
                Play a sound when new notifications arrive
              </span>
            </div>
            <button
              type="button"
              role="switch"
              aria-checked={settings.notificationSound}
              onClick={() =>
                update("notificationSound", !settings.notificationSound)
              }
              className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors ${
                settings.notificationSound
                  ? "bg-[var(--color-accent)]"
                  : "bg-[var(--color-border)]"
              }`}
            >
              <span
                className={`pointer-events-none inline-block h-5 w-5 rounded-full bg-white shadow-sm transition-transform ${
                  settings.notificationSound ? "translate-x-5" : "translate-x-0"
                }`}
              />
            </button>
          </label>

          {/* Email notifications */}
          <label className="flex items-center justify-between rounded-lg border border-[var(--color-border)] bg-[var(--color-bg-secondary)] px-4 py-3">
            <div>
              <span className="block text-sm text-[var(--color-text)]">
                Email notifications
              </span>
              <span className="block text-xs text-[var(--color-text-dim)]">
                Receive notifications via email for approvals and escalations
              </span>
            </div>
            <button
              type="button"
              role="switch"
              aria-checked={settings.emailNotifications}
              onClick={() =>
                update("emailNotifications", !settings.emailNotifications)
              }
              className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors ${
                settings.emailNotifications
                  ? "bg-[var(--color-accent)]"
                  : "bg-[var(--color-border)]"
              }`}
            >
              <span
                className={`pointer-events-none inline-block h-5 w-5 rounded-full bg-white shadow-sm transition-transform ${
                  settings.emailNotifications
                    ? "translate-x-5"
                    : "translate-x-0"
                }`}
              />
            </button>
          </label>
        </div>
      </div>

      {/* Reset */}
      <div className="flex justify-end">
        <button
          onClick={resetDefaults}
          className="rounded-lg border border-[var(--color-border)] px-4 py-2 text-xs font-medium text-[var(--color-text-muted)] hover:text-[var(--color-text)] hover:border-[var(--color-text-muted)] transition-colors"
        >
          Reset to defaults
        </button>
      </div>
    </div>
  );
}
