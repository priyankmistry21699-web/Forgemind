"use client";

import { useEffect, useState } from "react";
import { fetchPlannerResult } from "@/lib/planner";
import type { PlannerResult } from "@/types/planner";

interface PlannerResultViewProps {
  runId: string;
}

function SectionCard({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-bg-card)] p-4">
      <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-[var(--color-text-muted)]">
        {title}
      </h3>
      {children}
    </div>
  );
}

export function PlannerResultView({ runId }: PlannerResultViewProps) {
  const [result, setResult] = useState<PlannerResult | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    fetchPlannerResult(runId).then((data) => {
      if (!cancelled) {
        setResult(data);
        setLoading(false);
      }
    });
    return () => {
      cancelled = true;
    };
  }, [runId]);

  if (loading) {
    return (
      <div className="animate-pulse space-y-3">
        {[1, 2, 3].map((i) => (
          <div
            key={i}
            className="h-16 rounded-lg bg-[var(--color-bg-secondary)]"
          />
        ))}
      </div>
    );
  }

  if (!result) {
    return (
      <div className="rounded-lg border border-dashed border-[var(--color-border)] py-6 text-center">
        <p className="text-sm text-[var(--color-text-muted)]">
          No planning result available
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {result.overview && (
        <SectionCard title="Overview">
          <p className="text-sm leading-relaxed">{result.overview}</p>
        </SectionCard>
      )}

      {result.architecture_summary && (
        <SectionCard title="Architecture">
          <p className="text-sm leading-relaxed">
            {result.architecture_summary}
          </p>
        </SectionCard>
      )}

      {result.recommended_stack &&
        Object.keys(result.recommended_stack).length > 0 && (
          <SectionCard title="Recommended Stack">
            <div className="flex flex-wrap gap-2">
              {Object.entries(result.recommended_stack).map(([key, value]) => (
                <div
                  key={key}
                  className="rounded-md border border-[var(--color-border)] bg-[var(--color-bg-secondary)] px-3 py-1.5"
                >
                  <span className="text-xs font-medium text-[var(--color-text-muted)]">
                    {key}:{" "}
                  </span>
                  <span className="text-xs font-semibold">{String(value)}</span>
                </div>
              ))}
            </div>
          </SectionCard>
        )}

      {result.assumptions && result.assumptions.length > 0 && (
        <SectionCard title="Assumptions">
          <ul className="list-inside list-disc space-y-1">
            {result.assumptions.map((item, i) => (
              <li key={i} className="text-sm text-[var(--color-text-muted)]">
                {item}
              </li>
            ))}
          </ul>
        </SectionCard>
      )}

      {result.next_steps && result.next_steps.length > 0 && (
        <SectionCard title="Next Steps">
          <ol className="list-inside list-decimal space-y-1">
            {result.next_steps.map((item, i) => (
              <li key={i} className="text-sm text-[var(--color-text-muted)]">
                {item}
              </li>
            ))}
          </ol>
        </SectionCard>
      )}
    </div>
  );
}
