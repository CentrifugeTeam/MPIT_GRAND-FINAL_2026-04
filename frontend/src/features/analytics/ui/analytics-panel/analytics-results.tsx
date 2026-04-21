import { Card } from "@heroui/react";

import type {
  ChartPayloadShape,
  NlSqlWsPayload,
} from "@/entities/analytics";
import { SqlBlock } from "@/shared/ui/molecules/sql-block";
import { DataTablePreview } from "@/shared/ui/organisms/data-table-preview";
import type { InterpretationHint } from "../../lib/interpretation-hint";

import { ANALYTICS_TABLE_PREVIEW_MAX } from "../../config/constants";
import { AnalyticsCharts } from "../analytics-charts";

type TFn = (key: string, opts?: Record<string, unknown>) => string;

export type AnalyticsResultsProps = {
  t: TFn;
  result: NlSqlWsPayload;
  showChart: boolean;
  chartPayload: ChartPayloadShape | undefined;
  /** Если в ответе нет interpretation (например ошибка до воркера), показываем запасной hint с панели */
  interpretationFallback?: InterpretationHint | null;
};

export function AnalyticsResults({
  t,
  result,
  showChart,
  chartPayload,
  interpretationFallback: _interpretationFallback,
}: AnalyticsResultsProps) {
  const cp = chartPayload;
  /* Плашка «ясность формулировки» — временно скрыта
  const interpHint =
    interpretationToHint(result.interpretation) ?? interpretationFallback ?? null;
  */

  return (
    <div className="space-y-4">
      {/* <InterpretationBanner t={t} hint={interpHint} variant="compact" /> */}

      {result.status === "done" && result.nl_answer && (
        <Card className="border border-border bg-surface p-5 shadow-sm">
          <h3 className="mb-2 text-sm font-medium text-foreground">
            {t("home.analytics.nlAnswerTitle")}
          </h3>
          <p className="whitespace-pre-wrap text-sm leading-relaxed text-foreground">
            {result.nl_answer}
          </p>
        </Card>
      )}

      {result.status === "done" && result.report && (
        <Card className="border border-border bg-surface p-5 shadow-sm">
          <h3 className="mb-2 text-sm font-medium text-foreground">
            {t("home.analytics.reportTitle")}
          </h3>
          <p className="whitespace-pre-wrap text-sm leading-relaxed text-muted">
            {result.report}
          </p>
        </Card>
      )}

      {result.status === "done" && result.orchestrator?.risks_ru && (
        <Card className="border border-border bg-surface/80 p-4 shadow-sm">
          <h3 className="mb-1 text-xs font-medium uppercase tracking-wide text-muted">
            {t("home.analytics.orchestratorRisksTitle")}
          </h3>
          <p className="whitespace-pre-wrap text-sm text-foreground">
            {result.orchestrator.risks_ru}
          </p>
        </Card>
      )}

      {result.status === "error" && (
        <Card className="border-danger/40 bg-danger/5 p-4">
          <p className="text-danger text-sm font-medium">
            {result.error || t("home.analytics.errorGeneric")}
          </p>
        </Card>
      )}

      {(result.status === "done" || (result.status === "error" && result.sql)) && (
        <>
          {result.sql && (
            <Card className="border border-border bg-surface p-5 shadow-sm">
              <SqlBlock title={t("home.analytics.generatedSql")} sql={result.sql} />
              {result.explanation && (
                <p className="text-muted mt-4 border-t border-border pt-4 text-sm leading-relaxed">
                  {result.explanation}
                </p>
              )}
            </Card>
          )}

          {result.guard_warnings && result.guard_warnings.length > 0 && (
            <Card className="border-warning/40 bg-warning/5 p-4">
              <ul className="list-inside list-disc text-sm text-warning">
                {result.guard_warnings.map((w) => (
                  <li key={w}>{w}</li>
                ))}
              </ul>
            </Card>
          )}

          {showChart && cp && (
            <Card className="border border-border bg-surface p-5 shadow-sm">
              <h3 className="mb-4 text-sm font-medium text-foreground">
                {t("home.analytics.chartTitle")}
              </h3>
              <AnalyticsCharts payload={cp} />
            </Card>
          )}

          {(result.columns?.length ?? 0) > 0 && (
            <Card className="border border-border bg-surface p-5 shadow-sm">
              <h3 className="mb-4 text-sm font-medium text-foreground">
                {t("home.analytics.tableTitle")}
              </h3>
              <DataTablePreview
                columns={result.columns ?? []}
                rows={result.rows ?? []}
                emptyLabel={t("home.analytics.tableEmpty")}
                truncatedHint={t("home.analytics.tableTruncated", {
                  max: ANALYTICS_TABLE_PREVIEW_MAX,
                  total: result.rows?.length ?? 0,
                })}
                maxPreviewRows={ANALYTICS_TABLE_PREVIEW_MAX}
              />
              <p className="text-muted mt-3 text-xs">
                {t("home.analytics.rowCount", {
                  count: result.row_count ?? result.rows?.length ?? 0,
                })}
              </p>
            </Card>
          )}
        </>
      )}
    </div>
  );
}
