"use client";

import { useEffect, useState } from "react";
import {
  computeSLO,
  listAnomalies,
  listSLOs,
  triggerAnomalyScan,
  type SLOSummary,
} from "@/lib/slos";

const DEMO_PROJECT_ID = "00000000-0000-0000-0000-000000000001";

interface Anomaly {
  id: string;
  type: string;
  severity: string;
  title: string;
  metric_value: number | null;
  deviation_pct: number | null;
  resolved: boolean;
  detected_at: string;
}

export default function SLOsPage() {
  const [slos, setSlos] = useState<SLOSummary[]>([]);
  const [anomalies, setAnomalies] = useState<Anomaly[]>([]);
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const [s, a] = await Promise.allSettled([
          listSLOs(DEMO_PROJECT_ID),
          listAnomalies(DEMO_PROJECT_ID, false),
        ]);
        if (s.status === "fulfilled") setSlos(s.value);
        if (a.status === "fulfilled") setAnomalies(a.value as Anomaly[]);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to load");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  async function handleCompute(sloId: string) {
    const result = await computeSLO(DEMO_PROJECT_ID, sloId);
    setSlos((prev) =>
      prev.map((s) =>
        s.id === sloId
          ? { ...s, latest_attainment_pct: result.attainment_pct, latest_met: result.met }
          : s
      )
    );
  }

  async function handleScan() {
    setScanning(true);
    try {
      await triggerAnomalyScan(DEMO_PROJECT_ID);
      const updated = await listAnomalies(DEMO_PROJECT_ID, false);
      setAnomalies(updated as Anomaly[]);
    } finally {
      setScanning(false);
    }
  }

  const severityColor = (s: string) => {
    if (s === "critical") return "bg-red-100 text-red-800";
    if (s === "high") return "bg-orange-100 text-orange-800";
    if (s === "medium") return "bg-yellow-100 text-yellow-800";
    return "bg-gray-100 text-gray-600";
  };

  return (
    <div className="p-6 space-y-8">
      <h1 className="text-2xl font-bold">SLOs &amp; Anomalies</h1>

      {loading && <p className="text-muted-foreground">Loading…</p>}
      {error && <p className="text-destructive">{error}</p>}

      <section>
        <h2 className="text-lg font-semibold mb-3">Service Level Objectives</h2>
        {slos.length === 0 && !loading ? (
          <p className="text-muted-foreground text-sm">No SLOs defined.</p>
        ) : (
          <div className="rounded-lg border overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-muted">
                <tr>
                  <th className="px-4 py-2 text-left">Name</th>
                  <th className="px-4 py-2 text-left">Metric</th>
                  <th className="px-4 py-2 text-right">Threshold</th>
                  <th className="px-4 py-2 text-right">Target</th>
                  <th className="px-4 py-2 text-right">Attainment</th>
                  <th className="px-4 py-2 text-left">Status</th>
                  <th className="px-4 py-2" />
                </tr>
              </thead>
              <tbody>
                {slos.map((s) => (
                  <tr key={s.id} className="border-t">
                    <td className="px-4 py-2 font-medium">{s.name}</td>
                    <td className="px-4 py-2 text-xs font-mono">{s.metric}</td>
                    <td className="px-4 py-2 text-right">{s.threshold}</td>
                    <td className="px-4 py-2 text-right">{(s.target_pct * 100).toFixed(1)}%</td>
                    <td className="px-4 py-2 text-right">
                      {s.latest_attainment_pct !== undefined
                        ? `${(s.latest_attainment_pct * 100).toFixed(1)}%`
                        : "—"}
                    </td>
                    <td className="px-4 py-2">
                      {s.latest_met !== undefined ? (
                        <span
                          className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${
                            s.latest_met ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"
                          }`}
                        >
                          {s.latest_met ? "met" : "breached"}
                        </span>
                      ) : (
                        <span className="text-muted-foreground text-xs">—</span>
                      )}
                    </td>
                    <td className="px-4 py-2 text-right">
                      <button
                        onClick={() => handleCompute(s.id)}
                        className="text-xs underline text-primary hover:opacity-75"
                      >
                        Compute
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
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-lg font-semibold">Active Anomalies</h2>
          <button
            onClick={handleScan}
            disabled={scanning}
            className="text-sm px-3 py-1 rounded bg-primary text-primary-foreground hover:opacity-90 disabled:opacity-50"
          >
            {scanning ? "Scanning…" : "Run Scan"}
          </button>
        </div>
        {anomalies.length === 0 && !loading ? (
          <p className="text-muted-foreground text-sm">No active anomalies.</p>
        ) : (
          <div className="space-y-2">
            {anomalies.map((a) => (
              <div key={a.id} className="rounded-lg border p-3 flex items-start gap-3">
                <span className={`mt-0.5 px-2 py-0.5 rounded-full text-xs font-medium ${severityColor(a.severity)}`}>
                  {a.severity}
                </span>
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-sm">{a.title}</p>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    {a.type}
                    {a.deviation_pct !== null ? ` · ${a.deviation_pct.toFixed(0)}% deviation` : ""}
                    {" · "}
                    {new Date(a.detected_at).toLocaleString()}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
