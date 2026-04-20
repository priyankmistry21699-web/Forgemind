interface DataTableProps {
  columns: string[];
  rows: (string | number)[][];
}

/** Simple table for dashboard table widgets. Scrolls internally. */
export function DataTable({ columns, rows }: DataTableProps) {
  if (columns.length === 0 || rows.length === 0) {
    return (
      <div className="flex h-full w-full items-center justify-center text-xs text-[var(--color-text-dim)]">
        No rows to show
      </div>
    );
  }
  return (
    <div className="h-full w-full overflow-auto">
      <table className="w-full border-collapse text-left text-xs">
        <thead className="sticky top-0 bg-[var(--color-bg-card)] text-[var(--color-text-muted)]">
          <tr>
            {columns.map((c, i) => (
              <th
                key={i}
                className="border-b border-[var(--color-border-subtle)] px-3 py-2 font-medium uppercase tracking-wider"
              >
                {c}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, ri) => (
            <tr
              key={ri}
              className="hover:bg-[var(--color-bg-card-hover)]"
            >
              {columns.map((_, ci) => (
                <td
                  key={ci}
                  className="border-b border-[var(--color-border-subtle)] px-3 py-1.5 text-[var(--color-text)] tabular-nums"
                >
                  {typeof row[ci] === "number"
                    ? (row[ci] as number).toLocaleString(undefined, {
                        maximumFractionDigits: 2,
                      })
                    : (row[ci] ?? "")}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
