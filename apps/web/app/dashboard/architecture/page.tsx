"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  fetchArchitectureGraph,
  fetchDrifts,
  fetchArchitectureRules,
  fetchRuleResults,
  fetchRecommendations,
  fetchHealthScore,
} from "@/lib/architecture";
import type {
  ArchitectureGraph,
  ArchitectureDrift,
  ArchitectureRule,
  ArchitectureRuleResult,
  RefactorRecommendation,
  StructuralHealthScore,
} from "@/types/architecture";

/* ------------------------------------------------------------------ */
/*  Colour helpers                                                     */
/* ------------------------------------------------------------------ */

const SEVERITY_COLORS: Record<string, string> = {
  critical: "var(--color-red, #ef4444)",
  high: "var(--color-orange, #f97316)",
  medium: "var(--color-yellow, #eab308)",
  low: "var(--color-green, #22c55e)",
};

function severityBadge(level: string) {
  return (
    <span
      style={{
        display: "inline-block",
        padding: "2px 8px",
        borderRadius: 4,
        fontSize: 11,
        fontWeight: 600,
        color: "#fff",
        backgroundColor: SEVERITY_COLORS[level] ?? "var(--color-text-muted)",
      }}
    >
      {level.toUpperCase()}
    </span>
  );
}

/* ------------------------------------------------------------------ */
/*  Main page                                                          */
/* ------------------------------------------------------------------ */

/**
 * Read the active project id from the current URL.
 *
 * Evaluated on every render (instead of at module-load time) so the test
 * harness can set `window.location.search` between renders and so the page
 * naturally reacts to client-side navigation.
 */
function readProjectId(): string {
  if (typeof window === "undefined") return "";
  return new URLSearchParams(window.location.search).get("project") ?? "";
}

export default function ArchitectureDashboard() {
  const PROJECT_ID = readProjectId();
  const [graph, setGraph] = useState<ArchitectureGraph | null>(null);
  const [drifts, setDrifts] = useState<ArchitectureDrift[]>([]);
  const [rules, setRules] = useState<ArchitectureRule[]>([]);
  const [results, setResults] = useState<ArchitectureRuleResult[]>([]);
  const [recs, setRecs] = useState<RefactorRecommendation[]>([]);
  const [health, setHealth] = useState<StructuralHealthScore | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!PROJECT_ID) {
      setLoading(false);
      return;
    }

    async function load() {
      try {
        const [g, d, ru, re, rc, hs] = await Promise.all([
          fetchArchitectureGraph(PROJECT_ID),
          fetchDrifts(PROJECT_ID),
          fetchArchitectureRules(PROJECT_ID),
          fetchRuleResults(PROJECT_ID),
          fetchRecommendations(PROJECT_ID),
          fetchHealthScore(PROJECT_ID),
        ]);
        setGraph(g);
        setDrifts(d.items);
        setRules(ru.items);
        setResults(re.items);
        setRecs(rc.items);
        setHealth(hs);
      } catch (err: unknown) {
        setError(
          err instanceof Error
            ? err.message
            : "Failed to load architecture data",
        );
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [PROJECT_ID]);

  /* ─ No project selected ─ */
  if (!PROJECT_ID) {
    return (
      <div className="space-y-6">
        <Breadcrumb />
        <div
          style={{
            padding: 32,
            textAlign: "center",
            color: "var(--color-text-muted)",
          }}
        >
          Add <code>?project=&lt;id&gt;</code> to the URL to view a
          project&apos;s architecture.
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <Breadcrumb />

      {/* Page header */}
      <div className="flex items-center justify-between">
        <h1 style={{ fontSize: 24, fontWeight: 700 }}>
          Architecture Review Workspace
        </h1>
      </div>

      {loading && (
        <p style={{ color: "var(--color-text-muted)" }}>Loading...</p>
      )}
      {error && <p style={{ color: "var(--color-red, #ef4444)" }}>{error}</p>}

      {!loading && !error && (
        <>
          {/* Overview cards */}
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))",
              gap: 12,
            }}
          >
            <StatCard label="Components" value={graph?.node_count ?? 0} />
            <StatCard label="Dependencies" value={graph?.edge_count ?? 0} />
            <StatCard label="Drift Findings" value={drifts.length} />
            <StatCard
              label="Rule Violations"
              value={results.filter((r) => r.status === "violation").length}
            />
            <StatCard label="Recommendations" value={recs.length} />
          </div>

          {/* Health score */}
          {health && (
            <Section title="Structural Health Score">
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 24,
                  flexWrap: "wrap",
                }}
              >
                <div
                  style={{
                    width: 80,
                    height: 80,
                    borderRadius: "50%",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontSize: 24,
                    fontWeight: 700,
                    border: `3px solid ${
                      health.overall_score >= 80
                        ? "var(--color-green, #22c55e)"
                        : health.overall_score >= 50
                          ? "var(--color-yellow, #eab308)"
                          : "var(--color-red, #ef4444)"
                    }`,
                    color:
                      health.overall_score >= 80
                        ? "var(--color-green, #22c55e)"
                        : health.overall_score >= 50
                          ? "var(--color-yellow, #eab308)"
                          : "var(--color-red, #ef4444)",
                  }}
                >
                  {health.overall_score}
                </div>
                <div style={{ fontSize: 13 }}>
                  <div>
                    Component Coverage:{" "}
                    <strong>{health.component_coverage}%</strong>
                  </div>
                  <div>
                    Rule Compliance: <strong>{health.rule_compliance}%</strong>
                  </div>
                  <div>
                    Isolation Ratio: <strong>{health.isolation_ratio}%</strong>
                  </div>
                  <div>
                    Drift Penalty:{" "}
                    <strong style={{ color: "var(--color-red, #ef4444)" }}>
                      -{health.drift_penalty}
                    </strong>
                  </div>
                </div>
              </div>
            </Section>
          )}

          {/* Node type breakdown */}
          {graph && graph.nodes.length > 0 && (
            <Section title="Components by Type">
              <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                {Object.entries(
                  graph.nodes.reduce<Record<string, number>>((acc, n) => {
                    acc[n.node_type] = (acc[n.node_type] ?? 0) + 1;
                    return acc;
                  }, {}),
                ).map(([type, count]) => (
                  <span
                    key={type}
                    style={{
                      padding: "4px 10px",
                      borderRadius: 4,
                      fontSize: 12,
                      backgroundColor: "var(--color-surface, #1e1e2e)",
                      border: "1px solid var(--color-border, #333)",
                    }}
                  >
                    {type}: <strong>{count}</strong>
                  </span>
                ))}
              </div>
            </Section>
          )}

          {/* Drift findings */}
          {drifts.length > 0 && (
            <Section title={`Drift Findings (${drifts.length})`}>
              <table style={{ width: "100%", fontSize: 13 }}>
                <thead>
                  <tr
                    style={{
                      borderBottom: "1px solid var(--color-border, #333)",
                      textAlign: "left",
                    }}
                  >
                    <th style={{ padding: "6px 8px" }}>Severity</th>
                    <th style={{ padding: "6px 8px" }}>Title</th>
                    <th style={{ padding: "6px 8px" }}>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {drifts.slice(0, 20).map((d) => (
                    <tr
                      key={d.id}
                      style={{
                        borderBottom: "1px solid var(--color-border, #222)",
                      }}
                    >
                      <td style={{ padding: "6px 8px" }}>
                        {severityBadge(d.severity)}
                      </td>
                      <td style={{ padding: "6px 8px" }}>{d.title}</td>
                      <td style={{ padding: "6px 8px" }}>{d.status}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Section>
          )}

          {/* Rules */}
          {rules.length > 0 && (
            <Section title={`Architecture Rules (${rules.length})`}>
              <ul style={{ paddingLeft: 18, fontSize: 13, lineHeight: 1.8 }}>
                {rules.map((r) => (
                  <li key={r.id}>
                    <strong>{r.name}</strong>{" "}
                    <span style={{ color: "var(--color-text-muted)" }}>
                      [{r.category}]
                    </span>
                  </li>
                ))}
              </ul>
            </Section>
          )}

          {/* Rule violations */}
          {results.filter((r) => r.status === "violation").length > 0 && (
            <Section title="Rule Violations">
              <ul style={{ paddingLeft: 18, fontSize: 13, lineHeight: 1.8 }}>
                {results
                  .filter((r) => r.status === "violation")
                  .map((r) => (
                    <li key={r.id}>{r.message}</li>
                  ))}
              </ul>
            </Section>
          )}

          {/* Recommendations */}
          {recs.length > 0 && (
            <Section title={`Refactor Recommendations (${recs.length})`}>
              {recs.map((r, i) => (
                <div
                  key={i}
                  style={{
                    padding: 12,
                    marginBottom: 8,
                    borderRadius: 6,
                    backgroundColor: "var(--color-surface, #1e1e2e)",
                    border: "1px solid var(--color-border, #333)",
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: 8,
                      marginBottom: 4,
                    }}
                  >
                    {severityBadge(r.severity)}
                    <strong style={{ fontSize: 14 }}>{r.title}</strong>
                  </div>
                  <p
                    style={{
                      fontSize: 13,
                      color: "var(--color-text-muted)",
                      margin: 0,
                    }}
                  >
                    {r.description}
                  </p>
                </div>
              ))}
            </Section>
          )}
        </>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Shared layout components                                           */
/* ------------------------------------------------------------------ */

function Breadcrumb() {
  return (
    <div className="flex items-center gap-2 text-xs text-[var(--color-text-muted)]">
      <Link
        href="/dashboard"
        className="hover:text-[var(--color-text)] transition-colors"
      >
        Dashboard
      </Link>
      <span>/</span>
      <span className="text-[var(--color-text)]">Architecture</span>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <div
      style={{
        padding: 16,
        borderRadius: 8,
        backgroundColor: "var(--color-surface, #1e1e2e)",
        border: "1px solid var(--color-border, #333)",
        textAlign: "center",
      }}
    >
      <div style={{ fontSize: 28, fontWeight: 700 }}>{value}</div>
      <div
        style={{
          fontSize: 12,
          color: "var(--color-text-muted)",
          marginTop: 4,
        }}
      >
        {label}
      </div>
    </div>
  );
}

function Section({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div
      style={{
        padding: 16,
        borderRadius: 8,
        backgroundColor: "var(--color-surface-raised, #252538)",
        border: "1px solid var(--color-border, #333)",
      }}
    >
      <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12 }}>
        {title}
      </h2>
      {children}
    </div>
  );
}
