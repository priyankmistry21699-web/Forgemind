export function TopNav() {
  return (
    <header className="flex h-14 shrink-0 items-center justify-between border-b border-[var(--color-border)] bg-[var(--color-bg-secondary)] px-6">
      <div>
        <h2 className="text-sm font-medium text-[var(--color-text)]">
          Control Plane
        </h2>
      </div>

      <div className="flex items-center gap-3">
        {/* Placeholder for future: notifications, user menu */}
        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-[var(--color-bg-card)] text-xs font-medium text-[var(--color-text-muted)]">
          U
        </div>
      </div>
    </header>
  );
}
