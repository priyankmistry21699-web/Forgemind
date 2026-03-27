import Link from "next/link";

export default function HomePage() {
  return (
    <div className="relative flex min-h-screen flex-col items-center justify-center px-4 overflow-hidden">
      {/* Background glow effects */}
      <div
        className="pointer-events-none absolute top-[-20%] left-1/2 h-[600px] w-[600px] -translate-x-1/2 rounded-full opacity-20 blur-[120px]"
        style={{
          background:
            "radial-gradient(circle, var(--color-accent), transparent 70%)",
        }}
      />
      <div
        className="pointer-events-none absolute bottom-[-10%] right-[-10%] h-[400px] w-[400px] rounded-full opacity-10 blur-[100px]"
        style={{
          background: "radial-gradient(circle, #22c55e, transparent 70%)",
        }}
      />

      {/* Hero */}
      <div className="relative z-10 mx-auto max-w-2xl text-center">
        <div className="mb-8 inline-flex items-center gap-2 rounded-full border border-[var(--color-border)] bg-[var(--color-bg-secondary)] px-4 py-1.5 text-xs text-[var(--color-text-muted)]">
          <span className="inline-block h-2 w-2 rounded-full bg-[var(--color-success)] animate-pulse" />
          v0.1.0 — Development
        </div>

        <h1 className="mb-6 text-5xl font-bold tracking-tight sm:text-6xl lg:text-7xl">
          Forge
          <span className="bg-gradient-to-r from-[var(--color-accent)] to-[var(--color-accent-hover)] bg-clip-text text-transparent">
            Mind
          </span>
        </h1>

        <p className="mx-auto mb-10 max-w-lg text-base leading-relaxed text-[var(--color-text-muted)] sm:text-lg">
          A secure autonomous engineering platform that turns high-level goals
          into complete, connected, verifiable software systems.
        </p>

        <div className="flex items-center justify-center gap-4">
          <Link
            href="/dashboard"
            className="inline-flex items-center gap-2 rounded-lg bg-[var(--color-accent)] px-6 py-3 text-sm font-medium text-white shadow-lg shadow-[var(--color-accent)]/25 transition-all hover:bg-[var(--color-accent-hover)] hover:shadow-[var(--color-accent)]/40 hover:-translate-y-0.5"
          >
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <rect x="3" y="3" width="7" height="7" />
              <rect x="14" y="3" width="7" height="7" />
              <rect x="14" y="14" width="7" height="7" />
              <rect x="3" y="14" width="7" height="7" />
            </svg>
            Open Dashboard
          </Link>
          <a
            href="http://localhost:8000/docs"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 rounded-lg border border-[var(--color-border)] bg-[var(--color-bg-secondary)] px-6 py-3 text-sm font-medium text-[var(--color-text-muted)] transition-all hover:border-[var(--color-text-muted)] hover:text-[var(--color-text)] hover:-translate-y-0.5"
          >
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <polyline points="14 2 14 8 20 8" />
              <line x1="16" y1="13" x2="8" y2="13" />
              <line x1="16" y1="17" x2="8" y2="17" />
            </svg>
            API Docs
          </a>
        </div>
      </div>

      {/* Feature highlights */}
      <div className="relative z-10 mx-auto mt-24 grid max-w-3xl grid-cols-1 gap-4 sm:grid-cols-3">
        {[
          {
            icon: "🎯",
            title: "Goal-to-System",
            desc: "Describe an idea, get a complete system — architecture, code, connectors, tests.",
          },
          {
            icon: "🤖",
            title: "Dynamic Agents",
            desc: "The right AI team is assembled per project, not a fixed pipeline.",
          },
          {
            icon: "🛡️",
            title: "Trust & Governance",
            desc: "Every action has risk scores, evidence, replay, and approval gates.",
          },
        ].map((feature) => (
          <div
            key={feature.title}
            className="group rounded-xl border border-[var(--color-border)] bg-[var(--color-bg-secondary)] p-5 transition-all hover:border-[var(--color-accent)]/30 hover:bg-[var(--color-bg-card)]"
          >
            <div className="mb-3 text-2xl">{feature.icon}</div>
            <h3 className="mb-2 text-sm font-semibold">{feature.title}</h3>
            <p className="text-xs leading-relaxed text-[var(--color-text-muted)]">
              {feature.desc}
            </p>
          </div>
        ))}
      </div>

      {/* Subtle footer line */}
      <div className="relative z-10 mt-24 text-center">
        <p className="text-xs text-[var(--color-text-dim)]">
          Built with FastAPI · Next.js · LiteLLM · PostgreSQL
        </p>
      </div>
    </div>
  );
}
