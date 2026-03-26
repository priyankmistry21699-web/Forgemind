"use client";

import type { ExecutionEvent } from "@/types/execution-event";

const EVENT_STYLES: Record<string, { icon: string; color: string }> = {
  task_claimed: { icon: "▶", color: "text-blue-400" },
  task_completed: { icon: "✓", color: "text-green-400" },
  task_failed: { icon: "✗", color: "text-red-400" },
  artifact_created: { icon: "📄", color: "text-purple-400" },
  approval_requested: { icon: "⏸", color: "text-amber-400" },
  approval_resolved: { icon: "✓", color: "text-emerald-400" },
  run_started: { icon: "🚀", color: "text-indigo-400" },
  run_completed: { icon: "🏁", color: "text-green-400" },
  run_failed: { icon: "💥", color: "text-red-400" },
  plan_generated: { icon: "📋", color: "text-cyan-400" },
};

interface EventTimelineSectionProps {
  events: ExecutionEvent[];
}

export function EventTimelineSection({ events }: EventTimelineSectionProps) {
  if (events.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-[var(--color-border)] py-6 text-center">
        <p className="text-sm text-[var(--color-text-muted)]">
          No events recorded yet
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-0">
      {events.map((event, idx) => {
        const style = EVENT_STYLES[event.event_type] ?? {
          icon: "•",
          color: "text-zinc-400",
        };
        const isLast = idx === events.length - 1;

        return (
          <div key={event.id} className="flex gap-3">
            {/* Timeline line + icon */}
            <div className="flex flex-col items-center">
              <span className={`text-sm ${style.color}`}>{style.icon}</span>
              {!isLast && (
                <div className="w-px flex-1 bg-[var(--color-border)]" />
              )}
            </div>

            {/* Content */}
            <div className="pb-4 min-w-0 flex-1">
              <p className="text-sm">{event.summary}</p>
              <div className="mt-0.5 flex items-center gap-2 text-[11px] text-[var(--color-text-muted)]">
                <span>{new Date(event.created_at).toLocaleString()}</span>
                {event.agent_slug && (
                  <span className="rounded bg-[var(--color-bg-secondary)] px-1.5 py-0.5">
                    {event.agent_slug}
                  </span>
                )}
                <span className="rounded bg-[var(--color-bg-secondary)] px-1.5 py-0.5 uppercase">
                  {event.event_type.replace("_", " ")}
                </span>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
