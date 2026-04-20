import { Card } from "@heroui/react";

import type {
  ChartPayloadShape,
  NlSqlWsPayload,
} from "@/entities/analytics/types";
import { SqlBlock } from "@/shared/ui/sql-block";
import { DataTablePreview } from "@/shared/ui/data-table-preview";

import { ANALYTICS_TABLE_PREVIEW_MAX } from "../../config/constants";
import { AnalyticsCharts } from "../analytics-charts";
import type { InterpretationHint } from "@/features/analytics/ui/analytics-panel/interpretation-banner";
import {
  InterpretationBanner,
  interpretationToHint,
} from "./interpretation-banner";

type TFn = (key: string, opts?: Record<string, unknown>) => string;

export type AnalyticsResultsProps = {
  t: TFn;
  result: NlSqlWsPayload;
  showChart: boolean;
  chartPayload: ChartPayloadShape | undefined;
  /** Если в ответе нет interpretation (ошибка до воркера), показываем оценку с ask-async */
  interpretationFallback?: InterpretationHint | null;
};

export function AnalyticsResults({
  t,
  result,
  showChart,
  chartPayload,
  interpretationFallback,
}: AnalyticsResultsProps) {
  const cp = chartPayload;
  const interpHint =
    interpretationToHint(result.interpretation) ?? interpretationFallback ?? null;

  return (
    <div className="space-y-4">
      <InterpretationBanner t={t} hint={interpHint} variant="compact" />

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
                {result.guard_warnings.map((w, i) => (
                  <li key={i}>{w}</li>
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
