import { Card } from "@heroui/react";

import { ANALYTICS_TABLE_PREVIEW_MAX } from "../../config/constants";
import {
  nlChatHasSeriesChart,
  nlChatHasTablePreview,
} from "../../lib/nl-chat-viz";
import type { NlChatLine } from "../../lib/use-nl-orchestrator-chat";
import { AnalyticsCharts } from "../analytics-charts";
import { DataTablePreview } from "@/shared/ui/organisms/data-table-preview";

type TFn = (key: string, opts?: Record<string, unknown>) => string;

export type TranscriptVariant = "card" | "figma" | "grok";

const bubbleCard = {
  user: "ml-4 rounded-xl border border-border/60 bg-primary/10 px-3 py-2.5 text-sm",
  assistant: "mr-4 border-l-2 border-border pl-3 pr-1 py-2 text-sm",
  system: "text-muted border-l border-dashed border-border/70 pl-3 text-xs",
};

const bubbleFigma = {
  user: "ml-2 rounded-xl border border-[#28282c] bg-[#27272a]/80 px-3 py-2.5 text-sm text-[#fcfcfc]",
  assistant: "mr-2 border-l-2 border-[#3f3f46] pl-3 pr-1 py-2 text-sm text-[#fcfcfc]",
  system: "text-[#a1a1aa] border-l border-dashed border-[#28282c] pl-3 text-xs",
};

const bubbleGrok = {
  user: "ml-auto w-fit max-w-[min(85%,520px)] min-w-0 rounded-[22px] bg-[#27272a] px-4 py-3 text-left font-sans text-[15px] font-normal leading-relaxed text-[#fafafa] break-words",
  assistant:
    "w-full max-w-[min(720px,100%)] font-sans text-[15px] font-normal leading-relaxed text-[#e4e4e7]",
  system: "mx-auto max-w-[min(560px,100%)] text-center font-sans text-xs leading-snug text-[#71717a]",
};

export function NlChatTranscriptBlock({
  t,
  nlChatLines,
  variant,
  emptyLabel,
}: {
  t: TFn;
  nlChatLines: NlChatLine[];
  variant: TranscriptVariant;
  emptyLabel: string;
}) {
  const b =
    variant === "grok" ? bubbleGrok : variant === "figma" ? bubbleFigma : bubbleCard;
  const labelMuted =
    variant === "figma" || variant === "grok"
      ? "text-[#71717a] text-xs font-medium uppercase tracking-wide"
      : "text-muted text-xs font-medium uppercase tracking-wide";
  const preClass =
    variant === "figma" || variant === "grok"
      ? "whitespace-pre-wrap font-sans text-[inherit]"
      : "whitespace-pre-wrap font-sans text-foreground";
  const sqlBox =
    variant === "figma" || variant === "grok"
      ? "mt-3 overflow-x-auto rounded-xl border border-[#28282c] bg-[#0c0c0e] p-3 font-mono text-[12px] leading-snug text-[#d4d4d8]"
      : "mt-2 overflow-x-auto rounded-lg bg-black/5 p-2 text-xs text-foreground";
  const innerCard =
    variant === "figma" || variant === "grok"
      ? "mt-4 rounded-2xl border border-[#28282c] bg-[#09090b] p-4 shadow-none"
      : "border-border mt-3 border border-border/80 bg-surface/80 p-4 shadow-none";

  const wrapClass =
    variant === "grok"
      ? "w-full space-y-8 px-1 py-1"
      : variant === "figma"
        ? "max-h-[min(420px,45vh)] space-y-3 overflow-y-auto rounded-xl border border-[#28282c] bg-[#060607]/40 p-3"
        : "max-h-72 space-y-3 overflow-y-auto rounded-xl border border-border bg-default/25 p-3";

  const showRoleLabels = variant !== "grok";

  return (
    <div className={wrapClass}>
      {nlChatLines.length === 0 && (
        <p
          className={
            variant === "figma" || variant === "grok"
              ? "text-sm text-[#a1a1aa]"
              : "text-muted text-sm"
          }
        >
          {emptyLabel}
        </p>
      )}
      {nlChatLines.map((l) => (
        <div
          key={l.id}
          className={
            l.role === "user" ? b.user : l.role === "assistant" ? b.assistant : b.system
          }
        >
          {showRoleLabels && l.role !== "system" && (
            <span className={`mb-1 block ${labelMuted}`}>
              {l.role === "user"
                ? t("home.analytics.chatRoleUser")
                : t("home.analytics.chatRoleAssistant")}
            </span>
          )}
          <pre className={preClass}>{l.text}</pre>
          {l.sql && <pre className={sqlBox}>{l.sql}</pre>}
          {l.role === "assistant" &&
            l.chartPayload &&
            nlChatHasSeriesChart(l.chartPayload) && (
              <Card className={innerCard}>
                <h4 className={labelMuted + " mb-3"}>{t("home.analytics.chartTitle")}</h4>
                <AnalyticsCharts payload={l.chartPayload} />
              </Card>
            )}
          {l.role === "assistant" &&
            nlChatHasTablePreview(l.columns, l.rows) && (
              <Card className={innerCard}>
                <h4 className={labelMuted + " mb-3"}>{t("home.analytics.tableTitle")}</h4>
                <DataTablePreview
                  columns={l.columns ?? []}
                  rows={l.rows ?? []}
                  emptyLabel={t("home.analytics.tableEmpty")}
                  truncatedHint={t("home.analytics.tableTruncated", {
                    max: ANALYTICS_TABLE_PREVIEW_MAX,
                    total: l.rows?.length ?? 0,
                  })}
                  maxPreviewRows={ANALYTICS_TABLE_PREVIEW_MAX}
                />
                <p
                  className={
                    variant === "figma" || variant === "grok"
                      ? "mt-2 text-xs text-[#a1a1aa]"
                      : "text-muted mt-2 text-xs"
                  }
                >
                  {t("home.analytics.rowCount", {
                    count: l.rowCount ?? l.rows?.length ?? 0,
                  })}
                </p>
              </Card>
            )}
        </div>
      ))}
    </div>
  );
}
