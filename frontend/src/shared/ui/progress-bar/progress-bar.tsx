export function ProgressBar({ value }: { value: number }) {
  const v = Math.min(100, Math.max(0, value));
  return (
    <div className="space-y-2">
      <div className="flex justify-between text-xs text-muted">
        <span />
        <span>{Math.round(v)}%</span>
      </div>
      <div className="h-2.5 w-full overflow-hidden rounded-full bg-default">
        <div
          className="h-full rounded-full bg-accent transition-[width] duration-300 ease-out"
          style={{ width: `${v}%` }}
        />
      </div>
    </div>
  );
}
