type TInterp = (key: string, opts?: Record<string, unknown>) => string;
import type { InterpretationHint } from "@/features/analytics/lib/interpretation-hint";

export function InterpretationBanner({
  t,
  hint,
  variant = "default",
}: {
  t: TInterp;
  hint: InterpretationHint | null;
  variant?: "default" | "compact";
}) {
  if (!hint) return null;

  const pct = Math.round(hint.confidence * 100);
  const low = hint.confidence < 0.55;
  const mid = hint.confidence >= 0.55 && hint.confidence < 0.75;

  return (
    <div
      className={`rounded-xl border px-3 py-2.5 text-sm ${
        low
          ? "border-warning/50 bg-warning/10"
          : mid
            ? "border-border bg-surface-secondary/60"
            : "border-accent/25 bg-accent/5"
      }`}
    >
      <div className="flex flex-wrap items-center gap-2 font-medium text-foreground">
        <span>{t("home.analytics.interpretationConfidence", { pct })}</span>
        {hint.glossaryTermsCount != null && hint.glossaryTermsCount > 0 && (
          <span className="text-muted font-normal">
            · {t("home.analytics.glossaryTermsMatched", { count: hint.glossaryTermsCount })}
          </span>
        )}
      </div>
      {(hint.warnings.length > 0 || hint.suggestions.length > 0) && (
        <div className={`space-y-1 ${variant === "compact" ? "mt-1.5" : "mt-2"} text-xs`}>
          {hint.warnings.length > 0 && (
            <div>
              <span className="text-warning font-medium">
                {t("home.analytics.interpretationWarnings")}:{" "}
              </span>
              <ul className="mt-0.5 list-inside list-disc text-muted">
                {hint.warnings.map((w, i) => (
                  <li key={i}>{w}</li>
                ))}
              </ul>
            </div>
          )}
          {hint.suggestions.length > 0 && (
            <div>
              <span className="text-foreground font-medium">
                {t("home.analytics.interpretationSuggestions")}:{" "}
              </span>
              <ul className="mt-0.5 list-inside list-disc text-muted">
                {hint.suggestions.map((s, i) => (
                  <li key={i}>{s}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
