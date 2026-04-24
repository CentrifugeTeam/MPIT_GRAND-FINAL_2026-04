import { useCallback, useEffect, useRef, useState } from "react";

import { Icon } from "@iconify/react";
import { Card } from "@heroui/react";
import { motion } from "motion/react";

import type { NlChatLine } from "../../lib/use-nl-orchestrator-chat";

import { ANALYTICS_TABLE_PREVIEW_MAX } from "../../config/constants";
import {
  nlChatHasSeriesChart,
  nlChatHasTablePreview,
} from "../../lib/nl-chat-viz";
import { AnalyticsCharts } from "../analytics-charts";
import { FigmaSimpleTooltip } from "../figma-home/figma-simple-tooltip";
import { DataTablePreview } from "@/shared/ui/organisms/data-table-preview";

type TFn = (key: string, opts?: Record<string, unknown>) => string;

export type TranscriptVariant = "card" | "figma" | "grok";

export type NlChatAssistantActionHandlers = {
  onRetry: (payload: {
    assistantLineId: string;
    userMessage: string;
    userLineId: string | null;
  }) => void | Promise<void>;
  onCreateReportTask: (userQuestion: string) => void | Promise<void>;
};

function precedingUserForRetry(
  lines: NlChatLine[],
  assistantIndex: number,
): { text: string; lineId: string } | null {
  for (let i = assistantIndex - 1; i >= 0; i--) {
    if (lines[i]!.role === "user") {
      return { text: lines[i]!.text, lineId: lines[i]!.id };
    }
  }
  return null;
}

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

const iconMotionTransition = { type: "spring" as const, stiffness: 420, damping: 28 };

function GrokAssistantToolbar({
  t,
  plain,
  userCtx,
  assistantLineId,
  handlers,
  actionsLocked,
}: {
  t: TFn;
  plain: string;
  userCtx: { text: string; lineId: string } | null;
  assistantLineId: string;
  handlers: NlChatAssistantActionHandlers;
  actionsLocked: boolean;
}) {
  const [copyFlash, setCopyFlash] = useState(false);

  useEffect(() => {
    if (!copyFlash) return;
    const id = window.setTimeout(() => setCopyFlash(false), 1800);
    return () => window.clearTimeout(id);
  }, [copyFlash]);

  const handleCopy = useCallback(async () => {
    if (actionsLocked || !plain) return;
    try {
      await navigator.clipboard.writeText(plain);
      setCopyFlash(true);
    } catch {
      /* ignore */
    }
  }, [actionsLocked, plain]);

  const lockHint = t("home.analytics.chatActionsLocked");
  const copyTooltipLabel = actionsLocked
    ? lockHint
    : copyFlash
      ? t("home.analytics.chatCopied")
      : t("home.analytics.chatActionCopy");

  const iconWrap =
    "inline-flex size-9 shrink-0 cursor-pointer items-center justify-center rounded-xl text-[#71717a] transition-colors hover:bg-[#27272a]/80 hover:text-[#e4e4e7]";
  const iconWrapDisabled = "pointer-events-none cursor-not-allowed opacity-40";

  return (
    <div className="mt-3 flex flex-wrap items-center gap-0.5">
      {plain ? (
        <FigmaSimpleTooltip label={copyTooltipLabel} side="top">
          <motion.span
            className="inline-flex"
            whileHover={actionsLocked ? undefined : { scale: 1.06 }}
            whileTap={actionsLocked ? undefined : { scale: 0.94 }}
            transition={iconMotionTransition}
          >
            <button
              type="button"
              className={`${iconWrap} ${actionsLocked ? iconWrapDisabled : ""}`}
              aria-label={copyTooltipLabel}
              aria-disabled={actionsLocked}
              disabled={actionsLocked}
              onClick={() => void handleCopy()}
            >
              <Icon icon="mdi:content-copy" width={18} />
            </button>
          </motion.span>
        </FigmaSimpleTooltip>
      ) : null}
      {userCtx?.text?.trim() ? (
        <FigmaSimpleTooltip
          label={actionsLocked ? lockHint : t("home.analytics.chatActionRetry")}
          side="top"
        >
          <motion.span
            className="inline-flex"
            whileHover={actionsLocked ? undefined : { scale: 1.06 }}
            whileTap={actionsLocked ? undefined : { scale: 0.94 }}
            transition={iconMotionTransition}
          >
            <button
              type="button"
              className={`${iconWrap} ${actionsLocked ? iconWrapDisabled : ""}`}
              aria-label={t("home.analytics.chatActionRetry")}
              aria-disabled={actionsLocked}
              disabled={actionsLocked}
              onClick={() =>
                void handlers.onRetry({
                  assistantLineId,
                  userMessage: userCtx.text.trim(),
                  userLineId: userCtx.lineId,
                })
              }
            >
              <Icon icon="mdi:refresh" width={20} />
            </button>
          </motion.span>
        </FigmaSimpleTooltip>
      ) : null}
      {userCtx?.text?.trim() ? (
        <FigmaSimpleTooltip
          label={
            actionsLocked ? lockHint : t("home.analytics.chatActionCreateTask")
          }
          side="top"
        >
          <motion.span
            className="inline-flex"
            whileHover={actionsLocked ? undefined : { scale: 1.06 }}
            whileTap={actionsLocked ? undefined : { scale: 0.94 }}
            transition={iconMotionTransition}
          >
            <button
              type="button"
              className={`${iconWrap} ${actionsLocked ? iconWrapDisabled : ""}`}
              aria-label={t("home.analytics.chatActionCreateTask")}
              aria-disabled={actionsLocked}
              disabled={actionsLocked}
              onClick={() =>
                void handlers.onCreateReportTask(userCtx.text.trim())
              }
            >
              <Icon icon="mdi:clipboard-text-outline" width={20} />
            </button>
          </motion.span>
        </FigmaSimpleTooltip>
      ) : null}
    </div>
  );
}

export function NlChatTranscriptBlock({
  t,
  nlChatLines,
  variant,
  emptyLabel,
  assistantActionHandlers,
  assistantActionsLocked = false,
}: {
  t: TFn;
  nlChatLines: NlChatLine[];
  variant: TranscriptVariant;
  emptyLabel: string;
  assistantActionHandlers?: NlChatAssistantActionHandlers | null;
  /** Блокировать копирование / retry / задача, пока идёт запрос к модели. */
  assistantActionsLocked?: boolean;
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

  const containerRef = useRef<HTMLDivElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const isAtBottomRef = useRef(true);

  useEffect(() => {
    const sentinel = bottomRef.current;
    if (!sentinel) return;

    const root = variant !== "grok" ? containerRef.current : null;
    const observer = new IntersectionObserver(
      ([entry]) => {
        isAtBottomRef.current = entry.isIntersecting;
      },
      { root, threshold: 0 },
    );
    observer.observe(sentinel);
    return () => observer.disconnect();
  }, [variant]);

  useEffect(() => {
    if (isAtBottomRef.current) {
      bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
    }
  }, [nlChatLines]);

  const showRoleLabels = variant !== "grok";
  const showAssistantToolbar =
    variant === "grok" && assistantActionHandlers != null;

  const reasoningBox =
    variant === "grok" || variant === "figma"
      ? "mb-2 rounded-lg border border-[#3f3f46]/60 bg-[#18181b]/80 px-2.5 py-2"
      : "bg-muted/30 border-border/60 mb-2 rounded-lg border px-2.5 py-2";
  const reasoningPre =
    variant === "grok" || variant === "figma"
      ? "whitespace-pre-wrap font-sans text-[12px] leading-snug text-[#a1a1aa]"
      : "text-muted whitespace-pre-wrap font-sans text-xs leading-snug";
  const reasoningLabel =
    variant === "grok" || variant === "figma"
      ? "mb-1 block text-[10px] font-medium uppercase tracking-wide text-[#71717a]"
      : "text-muted mb-1 block text-[10px] font-medium uppercase tracking-wide";

  return (
    <div className={wrapClass} ref={containerRef}>
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
      {nlChatLines.map((l, lineIndex) => (
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
          {((l.role === "assistant" || l.role === "system") &&
            (l.reasoning || l.answerPending)) && (
            <div className={reasoningBox}>
              <span className={reasoningLabel}>
                {t("home.analytics.chatReasoningLabel")}
              </span>
              <pre className={reasoningPre}>
                {l.reasoning ||
                  (l.answerPending
                    ? t("home.analytics.chatReasoningLoading")
                    : "")}
              </pre>
            </div>
          )}
          <pre className={preClass}>
            {l.answerPending && !l.text.trim()
              ? t("home.analytics.chatAnswerComposing")
              : l.text}
          </pre>
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
          {showAssistantToolbar &&
            l.role === "assistant" &&
            !l.answerPending &&
            assistantActionHandlers && (
              <GrokAssistantToolbar
                t={t}
                plain={l.text.trim()}
                userCtx={precedingUserForRetry(nlChatLines, lineIndex)}
                assistantLineId={l.id}
                handlers={assistantActionHandlers}
                actionsLocked={assistantActionsLocked}
              />
            )}
        </div>
      ))}
      <div ref={bottomRef} />
    </div>
  );
}
