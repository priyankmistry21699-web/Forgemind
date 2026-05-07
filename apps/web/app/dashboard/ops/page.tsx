"use client";

import { useCallback, useEffect, useState } from "react";
import {
  fetchCacheStats,
  fetchJobs,
  fetchModelRouterStatus,
  fetchQueryStats,
  flushCache,
  triggerJob,
  type CacheStats,
  type JobInfo,
  type ModelRouterStatus,
  type QueryStat,
} from "@/lib/ops";

export default function OpsPage() {
  const [queryStats, setQueryStats] = useState<QueryStat[]>([]);
  const [cacheStats, setCacheStats] = useState<CacheStats | null>(null);
  const [jobs, setJobs] = useState<JobInfo[]>([]);
  const [modelRouter, setModelRouter] = useState<ModelRouterStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [flushing, setFlushing] = useState(false);

  const load = useCallback(async () => {
    try {
      const [qs, cs, js, mr] = await Promise.allSettled([
        fetchQueryStats(),
        fetchCacheStats(),
        fetchJobs(),
        fetchModelRouterStatus(),
      ]);
      if (qs.status === "fulfilled") setQueryStats(qs.value);
      if (cs.status === "fulfilled") setCacheStats(cs.value);
      if (js.status === "fulfilled") setJobs(js.value);
      if (mr.status === "fulfilled") setModelRouter(mr.value);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load ops data");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const handleFlushCache = async () => {
    setFlushing(true);
    try {
      await flushCache();
      await load();
    } finally {
      setFlushing(false);
    }
  };

  const handleTriggerJob = async (name: string) => {
    await triggerJob(name);
    await load();
  };

  if (loading) {
    return (
      <div className="p-6">
        <p className="text-sm text-muted-foreground">Loading ops data…</p>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-8">
      <div>
        <h1 className="text-2xl font-bold">Ops Dashboard</h1>
        <p className="text-sm text-muted-foreground">
          System health: caching, background jobs, query performance, and model routing.
        </p>
      </div>

      {error && (
        <div className="rounded border border-destructive bg-destructive/10 p-4 text-sm text-destructive">
          {error}
        </div>
      )}

      {/* Cache Stats */}
      <section>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-lg font-semibold">Cache</h2>
          <button
            onClick={handleFlushCache}
            disabled={flushing}
            className="rounded bg-secondary px-3 py-1.5 text-xs font-medium hover:bg-secondary/80 disabled:opacity-50"
          >
            {flushing ? "Flushing…" : "Flush Cache"}
          </button>
        </div>
        {cacheStats ? (
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            {[
              { label: "Local Size", value: `${cacheStats.local_size} / ${cacheStats.local_max_size}` },
              { label: "Hits", value: cacheStats.hits },
              { label: "Misses", value: cacheStats.misses },
              { label: "Hit Rate", value: `${(cacheStats.hit_rate * 100).toFixed(1)}%` },
            ].map((stat) => (
              <div key={stat.label} className="rounded border p-3">
                <p className="text-xs text-muted-foreground">{stat.label}</p>
                <p className="text-xl font-bold">{stat.value}</p>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">Cache stats unavailable</p>
        )}
      </section>

      {/* Background Jobs */}
      <section>
        <h2 className="text-lg font-semibold mb-3">Background Jobs</h2>
        {jobs.length === 0 ? (
          <p className="text-sm text-muted-foreground">No jobs registered</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left text-xs text-muted-foreground">
                  <th className="pb-2 font-medium">Job</th>
                  <th className="pb-2 font-medium">Last Run</th>
                  <th className="pb-2 font-medium">Status</th>
                  <th className="pb-2 font-medium"></th>
                </tr>
              </thead>
              <tbody>
                {jobs.map((job) => (
                  <tr key={job.name} className="border-b last:border-0">
                    <td className="py-2 font-mono">{job.name}</td>
                    <td className="py-2 text-muted-foreground">
                      {job.last_run_at
                        ? new Date(job.last_run_at).toLocaleString()
                        : "Never"}
                    </td>
                    <td className="py-2">
                      <span
                        className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
                          job.status === "ok"
                            ? "bg-green-100 text-green-800"
                            : "bg-yellow-100 text-yellow-800"
                        }`}
                      >
                        {job.status}
                      </span>
                    </td>
                    <td className="py-2 text-right">
                      <button
                        onClick={() => handleTriggerJob(job.name)}
                        className="rounded bg-primary px-2 py-1 text-xs text-primary-foreground hover:bg-primary/90"
                      >
                        Trigger
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {/* Slow Queries */}
      <section>
        <h2 className="text-lg font-semibold mb-3">Slow Queries</h2>
        {queryStats.length === 0 ? (
          <p className="text-sm text-muted-foreground">No slow queries recorded</p>
        ) : (
          <div className="space-y-2">
            {queryStats.map((q, i) => (
              <div key={i} className="rounded border p-3 text-xs">
                <div className="flex items-center justify-between mb-1">
                  <span className="font-medium text-destructive">
                    {q.duration_ms}ms
                  </span>
                  <span className="text-muted-foreground">
                    {new Date(q.timestamp).toLocaleTimeString()}
                  </span>
                </div>
                <pre className="overflow-x-auto text-muted-foreground whitespace-pre-wrap break-all">
                  {q.query}
                </pre>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Model Router */}
      <section>
        <h2 className="text-lg font-semibold mb-3">Model Router</h2>
        {modelRouter ? (
          <div className="space-y-2">
            <p className="text-xs text-muted-foreground">
              Config: {modelRouter.config_source}
            </p>
            <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-3">
              {Object.entries(modelRouter.models).map(([model, info]) => (
                <div key={model} className="rounded border p-3 text-sm">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs">{model}</span>
                    <span
                      className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
                        info.healthy
                          ? "bg-green-100 text-green-800"
                          : "bg-red-100 text-red-800"
                      }`}
                    >
                      {info.healthy ? "healthy" : "degraded"}
                    </span>
                  </div>
                  {info.error_count > 0 && (
                    <p className="mt-1 text-xs text-muted-foreground">
                      {info.error_count} errors
                    </p>
                  )}
                </div>
              ))}
            </div>
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">Model router status unavailable</p>
        )}
      </section>
    </div>
  );
}
