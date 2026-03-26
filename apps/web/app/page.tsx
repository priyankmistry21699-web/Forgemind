import Link from "next/link";

export default function HomePage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center px-4">
      {/* Hero */}
      <div className="mx-auto max-w-2xl text-center">
        <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-[var(--color-border)] bg-[var(--color-bg-secondary)] px-4 py-1.5 text-xs text-[var(--color-text-muted)]">
          <span className="inline-block h-1.5 w-1.5 rounded-full bg-[var(--color-success)]" />
          v0.1.0 — Development
        </div>

        <h1 className="mb-4 text-4xl font-bold tracking-tight sm:text-5xl">
          Forge
          <span className="text-[var(--color-accent)]">Mind</span>
        </h1>

        <p className="mb-8 text-lg leading-relaxed text-[var(--color-text-muted)]">
          A secure autonomous engineering platform that turns high-level goals
          into complete, connected, verifiable software systems — with
          architecture generation, connector intelligence, and long-term project
          health awareness.
        </p>

        <div className="flex items-center justify-center gap-4">
          <Link
            href="/dashboard"
            className="inline-flex items-center rounded-lg bg-[var(--color-accent)] px-5 py-2.5 text-sm font-medium text-white transition-colors hover:bg-[var(--color-accent-hover)]"
          >
            Open Dashboard
          </Link>
          <a
            href="http://localhost:8000/docs"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center rounded-lg border border-[var(--color-border)] px-5 py-2.5 text-sm font-medium text-[var(--color-text-muted)] transition-colors hover:border-[var(--color-text-muted)]"
          >
            API Docs
          </a>
        </div>
      </div>

      {/* Feature highlights */}
      <div className="mx-auto mt-20 grid max-w-3xl grid-cols-1 gap-4 sm:grid-cols-3">
        {[
          {
            title: "Goal-to-System",
            desc: "Describe an idea, get a complete system — architecture, code, connectors, tests.",
          },
          {
            title: "Dynamic Agents",
            desc: "The right AI team is assembled per project, not a fixed pipeline.",
          },
          {
            title: "Trust & Governance",
            desc: "Every action has risk scores, evidence, replay, and approval gates.",
          },
        ].map((feature) => (
          <div
            key={feature.title}
            className="rounded-lg border border-[var(--color-border)] bg-[var(--color-bg-secondary)] p-4"
          >
            <h3 className="mb-1 text-sm font-semibold">{feature.title}</h3>
            <p className="text-xs leading-relaxed text-[var(--color-text-muted)]">
              {feature.desc}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
