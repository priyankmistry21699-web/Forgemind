"use client";

import { useCallback, useEffect, useState } from "react";
import {
  fetchProjectReleasePackages,
  evaluateGates,
  fetchRollbackReadiness,
} from "@/lib/release-ops";
import type {
  ReleasePackage,
  GateEvaluation,
  RollbackReadiness,
} from "@/types/release-ops";

const STATUS_STYLES: Record<string, string> = {
  draft: "background: var(--color-bg-muted); color: var(--color-text-muted)",
  ready: "background: #dcfce7; color: #166534",
  gated: "background: #fef9c3; color: #854d0e",
  approved: "background: #dbeafe; color: #1e40af",
  deployed: "background: #d1fae5; color: #065f46",
  rolled_back: "background: #fecaca; color: #991b1b",
  failed: "background: #fecaca; color: #991b1b",
};

export default function ReleasesPage() {
  const [releases, setReleases] = useState<ReleasePackage[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [projectId, setProjectId] = useState("");
  const [selectedPkg, setSelectedPkg] = useState<ReleasePackage | null>(null);
  const [gateResults, setGateResults] = useState<GateEvaluation | null>(null);
  const [rollback, setRollback] = useState<RollbackReadiness | null>(null);

  const loadReleases = useCallback(async () => {
    if (!projectId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await fetchProjectReleasePackages(projectId);
      setReleases(data.items);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load releases");
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    if (projectId) loadReleases();
  }, [projectId, loadReleases]);

  const handleEvaluateGates = async (pkg: ReleasePackage) => {
    try {
      const result = await evaluateGates(pkg.id);
      setGateResults(result);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Gate evaluation failed");
    }
  };

  const handleCheckRollback = async (pkg: ReleasePackage) => {
    try {
      const result = await fetchRollbackReadiness(pkg.id);
      setRollback(result);
    } catch (err: unknown) {
      setError(
        err instanceof Error ? err.message : "Rollback check failed",
      );
    }
  };

  return (
    <div style={{ padding: "2rem", maxWidth: "1200px", margin: "0 auto" }}>
      {/* Header */}
      <div style={{ marginBottom: "1.5rem" }}>
        <h1
          style={{
            fontSize: "1.5rem",
            fontWeight: 700,
            color: "var(--color-text-primary)",
          }}
        >
          Release Operations
        </h1>
        <p style={{ color: "var(--color-text-muted)", marginTop: "0.25rem" }}>
          Manage release packages, gates, and rollback readiness.
        </p>
      </div>

      {/* Project ID filter */}
      <div style={{ marginBottom: "1.5rem", display: "flex", gap: "0.5rem" }}>
        <input
          type="text"
          value={projectId}
          onChange={(e) => setProjectId(e.target.value)}
          placeholder="Enter Project ID"
          style={{
            padding: "0.5rem 0.75rem",
            border: "1px solid var(--color-border)",
            borderRadius: "6px",
            flex: 1,
            maxWidth: "400px",
            background: "var(--color-bg-card)",
            color: "var(--color-text-primary)",
          }}
        />
        <button
          onClick={loadReleases}
          style={{
            padding: "0.5rem 1rem",
            background: "var(--color-primary)",
            color: "#fff",
            border: "none",
            borderRadius: "6px",
            cursor: "pointer",
          }}
        >
          Load
        </button>
      </div>

      {error && (
        <div
          style={{
            padding: "0.75rem",
            background: "#fecaca",
            color: "#991b1b",
            borderRadius: "6px",
            marginBottom: "1rem",
          }}
        >
          {error}
        </div>
      )}

      {loading && projectId && (
        <p style={{ color: "var(--color-text-muted)" }}>Loading...</p>
      )}

      {/* Release cards */}
      {!loading && releases.length === 0 && projectId && (
        <p style={{ color: "var(--color-text-muted)" }}>
          No release packages found.
        </p>
      )}

      <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
        {releases.map((pkg) => (
          <div
            key={pkg.id}
            style={{
              border: "1px solid var(--color-border)",
              borderRadius: "8px",
              padding: "1rem",
              background: "var(--color-bg-card)",
              cursor: "pointer",
            }}
            onClick={() => setSelectedPkg(pkg)}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
              }}
            >
              <div>
                <span style={{ fontWeight: 600, fontSize: "1.1rem" }}>
                  v{pkg.version}
                </span>
                <span
                  style={{
                    marginLeft: "0.75rem",
                    padding: "0.15rem 0.5rem",
                    borderRadius: "4px",
                    fontSize: "0.8rem",
                    ...(STATUS_STYLES[pkg.status]
                      ? Object.fromEntries(
                          STATUS_STYLES[pkg.status]
                            .split(";")
                            .map((s: string) => {
                              const [k, v] = s.split(":").map((x) => x.trim());
                              return [k, v];
                            }),
                        )
                      : {}),
                  }}
                >
                  {pkg.status}
                </span>
              </div>
              <span
                style={{ fontSize: "0.8rem", color: "var(--color-text-muted)" }}
              >
                {new Date(pkg.created_at).toLocaleDateString()}
              </span>
            </div>
            {pkg.summary && (
              <p
                style={{
                  marginTop: "0.5rem",
                  fontSize: "0.9rem",
                  color: "var(--color-text-muted)",
                }}
              >
                {pkg.summary}
              </p>
            )}
            <div style={{ marginTop: "0.75rem", display: "flex", gap: "0.5rem" }}>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleEvaluateGates(pkg);
                }}
                style={{
                  padding: "0.3rem 0.6rem",
                  fontSize: "0.8rem",
                  border: "1px solid var(--color-border)",
                  borderRadius: "4px",
                  background: "var(--color-bg-muted)",
                  cursor: "pointer",
                }}
              >
                Evaluate Gates
              </button>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleCheckRollback(pkg);
                }}
                style={{
                  padding: "0.3rem 0.6rem",
                  fontSize: "0.8rem",
                  border: "1px solid var(--color-border)",
                  borderRadius: "4px",
                  background: "var(--color-bg-muted)",
                  cursor: "pointer",
                }}
              >
                Rollback Readiness
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Gate results panel */}
      {gateResults && (
        <div
          style={{
            marginTop: "1.5rem",
            border: "1px solid var(--color-border)",
            borderRadius: "8px",
            padding: "1rem",
            background: "var(--color-bg-card)",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between" }}>
            <h2 style={{ fontSize: "1.1rem", fontWeight: 600 }}>
              Gate Evaluation
            </h2>
            <button
              onClick={() => setGateResults(null)}
              style={{ cursor: "pointer", border: "none", background: "none" }}
            >
              ✕
            </button>
          </div>
          <div
            style={{
              marginTop: "0.5rem",
              display: "flex",
              gap: "1rem",
              fontSize: "0.9rem",
            }}
          >
            <span style={{ color: "#166534" }}>
              ✓ {gateResults.passed} passed
            </span>
            <span style={{ color: "#991b1b" }}>
              ✗ {gateResults.failed} failed
            </span>
            <span>
              Status: <strong>{gateResults.package_status}</strong>
            </span>
          </div>
          <div style={{ marginTop: "0.75rem" }}>
            {gateResults.gate_results.map((g, i) => (
              <div
                key={i}
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  padding: "0.3rem 0",
                  borderBottom: "1px solid var(--color-border)",
                  fontSize: "0.85rem",
                }}
              >
                <span>{g.gate}</span>
                <span
                  style={{
                    color:
                      g.status === "passed"
                        ? "#166534"
                        : g.status === "failed"
                          ? "#991b1b"
                          : "var(--color-text-muted)",
                  }}
                >
                  {g.status === "passed" ? "✓" : g.status === "failed" ? "✗" : "—"}{" "}
                  {g.detail}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Rollback readiness panel */}
      {rollback && (
        <div
          style={{
            marginTop: "1.5rem",
            border: "1px solid var(--color-border)",
            borderRadius: "8px",
            padding: "1rem",
            background: "var(--color-bg-card)",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between" }}>
            <h2 style={{ fontSize: "1.1rem", fontWeight: 600 }}>
              Rollback Readiness
            </h2>
            <button
              onClick={() => setRollback(null)}
              style={{ cursor: "pointer", border: "none", background: "none" }}
            >
              ✕
            </button>
          </div>
          <div style={{ marginTop: "0.5rem", fontSize: "0.9rem" }}>
            <p>
              Ready:{" "}
              <strong
                style={{
                  color: rollback.is_rollback_ready ? "#166534" : "#991b1b",
                }}
              >
                {rollback.is_rollback_ready ? "Yes" : "No"}
              </strong>{" "}
              — Risk:{" "}
              <strong
                style={{
                  color:
                    rollback.risk_level === "low"
                      ? "#166534"
                      : rollback.risk_level === "high"
                        ? "#991b1b"
                        : "#854d0e",
                }}
              >
                {rollback.risk_level}
              </strong>
            </p>
          </div>
          <div style={{ marginTop: "0.5rem" }}>
            <h3 style={{ fontSize: "0.9rem", fontWeight: 600 }}>
              Recovery Points ({rollback.recovery_point_count})
            </h3>
            {rollback.recovery_points.map((rp, i) => (
              <div
                key={i}
                style={{
                  fontSize: "0.85rem",
                  padding: "0.25rem 0",
                  borderBottom: "1px solid var(--color-border)",
                }}
              >
                [{rp.type}] {rp.label}
              </div>
            ))}
          </div>
          {rollback.strategies.length > 0 && (
            <div style={{ marginTop: "0.75rem" }}>
              <h3 style={{ fontSize: "0.9rem", fontWeight: 600 }}>
                Strategies
              </h3>
              {rollback.strategies.map((s, i) => (
                <div key={i} style={{ fontSize: "0.85rem", padding: "0.2rem 0" }}>
                  <strong>{s.strategy}</strong>: {s.description}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Selected package detail */}
      {selectedPkg && (
        <div
          style={{
            marginTop: "1.5rem",
            border: "1px solid var(--color-border)",
            borderRadius: "8px",
            padding: "1rem",
            background: "var(--color-bg-card)",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between" }}>
            <h2 style={{ fontSize: "1.1rem", fontWeight: 600 }}>
              v{selectedPkg.version} — Details
            </h2>
            <button
              onClick={() => setSelectedPkg(null)}
              style={{ cursor: "pointer", border: "none", background: "none" }}
            >
              ✕
            </button>
          </div>
          <div
            style={{
              marginTop: "0.5rem",
              fontSize: "0.85rem",
              display: "grid",
              gridTemplateColumns: "1fr 1fr",
              gap: "0.5rem",
            }}
          >
            <div>
              <strong>Run ID:</strong> {selectedPkg.run_id}
            </div>
            <div>
              <strong>Status:</strong> {selectedPkg.status}
            </div>
            <div>
              <strong>Environment:</strong>{" "}
              {selectedPkg.target_environment_id ?? "—"}
            </div>
            <div>
              <strong>Created:</strong>{" "}
              {new Date(selectedPkg.created_at).toLocaleString()}
            </div>
          </div>
          {selectedPkg.confidence_snapshot && (
            <div style={{ marginTop: "0.75rem" }}>
              <strong style={{ fontSize: "0.9rem" }}>Confidence:</strong>
              <pre
                style={{
                  marginTop: "0.25rem",
                  fontSize: "0.8rem",
                  background: "var(--color-bg-muted)",
                  padding: "0.5rem",
                  borderRadius: "4px",
                  overflow: "auto",
                  maxHeight: "150px",
                }}
              >
                {JSON.stringify(selectedPkg.confidence_snapshot, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
