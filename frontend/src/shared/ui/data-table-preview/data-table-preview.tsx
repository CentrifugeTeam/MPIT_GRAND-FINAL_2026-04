import { formatTableCell } from "./lib/format-cell";

export type DataTablePreviewProps = {
  columns: string[];
  rows: Record<string, unknown>[];
  emptyLabel: string;
  truncatedHint: string;
  maxPreviewRows?: number;
};

export function DataTablePreview({
  columns,
  rows,
  emptyLabel,
  truncatedHint,
  maxPreviewRows = 10_000,
}: DataTablePreviewProps) {
  if (!columns.length || !rows.length) {
    return (
      <p className="text-sm text-muted">{emptyLabel}</p>
    );
  }
  const shown = rows.slice(0, maxPreviewRows);
  return (
    <div className="max-h-[min(480px,70vh)] overflow-auto rounded-xl border border-border">
      <table className="w-full min-w-[320px] text-left text-sm">
        <thead className="bg-surface-secondary text-xs uppercase tracking-wide text-muted sticky top-0">
          <tr>
            {columns.map((c) => (
              <th key={c} className="px-3 py-2 font-medium">
                {c}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {shown.map((row, i) => (
            <tr key={i} className="hover:bg-default/40">
              {columns.map((c) => (
                <td key={c} className="px-3 py-2 font-mono text-xs text-foreground">
                  {formatTableCell(row[c])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {rows.length > maxPreviewRows && (
        <p className="border-t border-border px-3 py-2 text-xs text-muted">
          {truncatedHint}
        </p>
      )}
    </div>
  );
}
