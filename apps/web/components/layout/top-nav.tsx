export function TopNav() {
  return (
    <header className="flex h-14 shrink-0 items-center justify-between border-b border-[var(--color-border)] bg-[var(--color-bg-secondary)]/80 backdrop-blur-sm px-6">
      <div className="flex items-center gap-3">
        <h2 className="text-sm font-medium text-[var(--color-text)]">
          Control Plane
        </h2>
        <span className="hidden sm:inline-flex items-center rounded-full bg-[var(--color-success-dim)] px-2 py-0.5 text-[10px] font-medium text-[var(--color-success)]">
          <span className="mr-1 inline-block h-1.5 w-1.5 rounded-full bg-[var(--color-success)] animate-pulse" />
          Online
        </span>
      </div>

      <div className="flex items-center gap-2">
        {/* Notification bell */}
        <button className="flex h-8 w-8 items-center justify-center rounded-lg text-[var(--color-text-muted)] transition-colors hover:bg-[var(--color-bg-card)] hover:text-[var(--color-text)]">
          <svg
            width="15"
            height="15"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
            <path d="M13.73 21a2 2 0 0 1-3.46 0" />
          </svg>
        </button>
        {/* User avatar */}
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-[var(--color-accent)] to-[var(--color-accent-hover)] text-xs font-bold text-white shadow-sm">
          U
        </div>
      </div>
    </header>
  );
}
