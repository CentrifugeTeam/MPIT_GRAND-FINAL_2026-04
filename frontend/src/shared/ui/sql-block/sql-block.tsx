export function SqlBlock({ title, sql }: { title: string; sql: string }) {
  return (
    <div className="space-y-2">
      <h3 className="text-sm font-medium text-foreground">{title}</h3>
      <pre className="max-h-48 overflow-auto rounded-xl border border-border bg-surface-secondary p-4 font-mono text-xs leading-relaxed text-foreground">
        {sql}
      </pre>
    </div>
  );
}
