"use client";

import { useEffect, useState } from "react";
import { listSchedules, listTriggerRules, pauseSchedule, resumeSchedule, type CronTrigger, type TriggerRule } from "@/lib/schedules";

const DEMO_PROJECT_ID = "00000000-0000-0000-0000-000000000001";

export default function SchedulesPage() {
  const [schedules, setSchedules] = useState<CronTrigger[]>([]);
  const [rules, setRules] = useState<TriggerRule[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const [s, r] = await Promise.allSettled([
          listSchedules(DEMO_PROJECT_ID),
          listTriggerRules(DEMO_PROJECT_ID),
        ]);
        if (s.status === "fulfilled") setSchedules(s.value);
        if (r.status === "fulfilled") setRules(r.value);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to load");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  async function toggleSchedule(s: CronTrigger) {
    if (s.status === "active") {
      await pauseSchedule(DEMO_PROJECT_ID, s.id);
    } else {
      await resumeSchedule(DEMO_PROJECT_ID, s.id);
    }
    setSchedules((prev) =>
      prev.map((x) =>
        x.id === s.id ? { ...x, status: s.status === "active" ? "paused" : "active" } : x
      )
    );
  }

  return (
    <div className="p-6 space-y-8">
      <h1 className="text-2xl font-bold">Schedules &amp; Triggers</h1>

      {loading && <p className="text-muted-foreground">Loading…</p>}
      {error && <p className="text-destructive">{error}</p>}

      <section>
        <h2 className="text-lg font-semibold mb-3">Cron Schedules</h2>
        {schedules.length === 0 && !loading ? (
          <p className="text-muted-foreground text-sm">No schedules configured.</p>
        ) : (
          <div className="rounded-lg border overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-muted">
                <tr>
                  <th className="px-4 py-2 text-left">Name</th>
                  <th className="px-4 py-2 text-left">Cron</th>
                  <th className="px-4 py-2 text-left">Status</th>
                  <th className="px-4 py-2 text-right">Fired</th>
                  <th className="px-4 py-2 text-left">Last Run</th>
                  <th className="px-4 py-2" />
                </tr>
              </thead>
              <tbody>
                {schedules.map((s) => (
                  <tr key={s.id} className="border-t">
                    <td className="px-4 py-2 font-medium">{s.name}</td>
                    <td className="px-4 py-2 font-mono text-xs">{s.cron_expression}</td>
                    <td className="px-4 py-2">
                      <span
                        className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${
                          s.status === "active"
                            ? "bg-green-100 text-green-800"
                            : "bg-yellow-100 text-yellow-800"
                        }`}
                      >
                        {s.status}
                      </span>
                    </td>
                    <td className="px-4 py-2 text-right">{s.fire_count}</td>
                    <td className="px-4 py-2 text-muted-foreground text-xs">
                      {s.last_fired_at ? new Date(s.last_fired_at).toLocaleString() : "—"}
                    </td>
                    <td className="px-4 py-2 text-right">
                      <button
                        onClick={() => toggleSchedule(s)}
                        className="text-xs underline text-primary hover:opacity-75"
                      >
                        {s.status === "active" ? "Pause" : "Resume"}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section>
        <h2 className="text-lg font-semibold mb-3">Event Trigger Rules</h2>
        {rules.length === 0 && !loading ? (
          <p className="text-muted-foreground text-sm">No trigger rules configured.</p>
        ) : (
          <div className="rounded-lg border overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-muted">
                <tr>
                  <th className="px-4 py-2 text-left">Name</th>
                  <th className="px-4 py-2 text-left">Event</th>
                  <th className="px-4 py-2 text-left">Enabled</th>
                  <th className="px-4 py-2 text-right">Fired</th>
                </tr>
              </thead>
              <tbody>
                {rules.map((r) => (
                  <tr key={r.id} className="border-t">
                    <td className="px-4 py-2 font-medium">{r.name}</td>
                    <td className="px-4 py-2 font-mono text-xs">{r.event_type}</td>
                    <td className="px-4 py-2">
                      <span
                        className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${
                          r.enabled ? "bg-green-100 text-green-800" : "bg-gray-100 text-gray-600"
                        }`}
                      >
                        {r.enabled ? "enabled" : "disabled"}
                      </span>
                    </td>
                    <td className="px-4 py-2 text-right">{r.fire_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
