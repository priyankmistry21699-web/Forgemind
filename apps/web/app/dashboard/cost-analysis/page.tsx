"use client";

import { useEffect, useState } from "react";
import { getCostForecast, type BudgetForecast } from "@/lib/cost-attribution";

const DEMO_PROJECT_ID = "00000000-0000-0000-0000-000000000001";

export default function CostAnalysisPage() {
  const [forecast, setForecast] = useState<BudgetForecast | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const f = await getCostForecast(DEMO_PROJECT_ID);
        setForecast(f);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to load");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const agentBreakdown = forecast?.breakdown_by_agent
    ? Object.entries(forecast.breakdown_by_agent).sort(([, a], [, b]) => (b as number) - (a as number))
    : [];

  return (
    <div className="p-6 space-y-8">
      <h1 className="text-2xl font-bold">Cost Analysis</h1>

      {loading && <p className="text-muted-foreground">Loading…</p>}
      {error && <p className="text-destructive">{error}</p>}

      {forecast && (
        <>
          <section className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard label="Month" value={forecast.forecast_month} />
            <StatCard
              label="Actual Spend"
              value={`$${forecast.actual_spend_usd.toFixed(2)}`}
            />
            <StatCard
              label="Forecasted"
              value={`$${forecast.forecasted_spend_usd.toFixed(2)}`}
              highlight={forecast.will_exceed_budget}
            />
            <StatCard
              label="Burn Rate"
              value={`$${forecast.burn_rate_usd_per_day.toFixed(2)}/day`}
            />
            {forecast.budget_usd !== null && (
              <StatCard label="Budget" value={`$${forecast.budget_usd.toFixed(2)}`} />
            )}
            <StatCard label="Days Remaining" value={String(forecast.days_remaining)} />
            <StatCard
              label="Confidence"
              value={`${(forecast.confidence * 100).toFixed(0)}%`}
            />
            <StatCard
              label="Will Exceed Budget"
              value={forecast.will_exceed_budget ? "Yes" : "No"}
              highlight={forecast.will_exceed_budget}
            />
          </section>

          {agentBreakdown.length > 0 && (
            <section>
              <h2 className="text-lg font-semibold mb-3">Cost by Agent</h2>
              <div className="rounded-lg border overflow-hidden">
                <table className="w-full text-sm">
                  <thead className="bg-muted">
                    <tr>
                      <th className="px-4 py-2 text-left">Agent</th>
                      <th className="px-4 py-2 text-right">Cost (USD)</th>
                      <th className="px-4 py-2 text-right">Share</th>
                    </tr>
                  </thead>
                  <tbody>
                    {agentBreakdown.map(([agent, cost]) => (
                      <tr key={agent} className="border-t">
                        <td className="px-4 py-2 font-medium">{agent}</td>
                        <td className="px-4 py-2 text-right">${(cost as number).toFixed(4)}</td>
                        <td className="px-4 py-2 text-right">
                          {forecast.actual_spend_usd > 0
                            ? `${(((cost as number) / forecast.actual_spend_usd) * 100).toFixed(1)}%`
                            : "—"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          )}
        </>
      )}
    </div>
  );
}

function StatCard({
  label,
  value,
  highlight = false,
}: {
  label: string;
  value: string;
  highlight?: boolean;
}) {
  return (
    <div className={`rounded-lg border p-4 ${highlight ? "border-destructive bg-destructive/5" : ""}`}>
      <p className="text-xs text-muted-foreground uppercase tracking-wide">{label}</p>
      <p className={`text-xl font-semibold mt-1 ${highlight ? "text-destructive" : ""}`}>{value}</p>
    </div>
  );
}
