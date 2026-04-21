import type React from "react";
import { Icon } from "@iconify/react";

import type { AnalyticsDataSourceItem } from "../../api/analytics-api";
import type { FigmaTranslateFn } from "../../config/figma-analytics-faq";
import { FigmaSimpleTooltip } from "./figma-simple-tooltip";

export type FigmaNlComposerProps = {
  t: FigmaTranslateFn;
  question: string;
  composerBusy: boolean;
  nlChatReady: boolean;
  dataSourcesLoaded: boolean;
  dataSources: AnalyticsDataSourceItem[];
  sourceButtonLabel: string;
  onOpenSourceModal: () => void;
  onQuestionChange: (v: string) => void;
  onSend: () => void;
  onVoiceOpen: () => void;
};

export function FigmaNlComposer({
  t,
  question,
  composerBusy,
  nlChatReady,
  dataSourcesLoaded,
  dataSources,
  sourceButtonLabel,
  onOpenSourceModal,
  onQuestionChange,
  onSend,
  onVoiceOpen,
}: FigmaNlComposerProps) {
  return (
    <div className="relative w-full shrink-0 rounded-3xl bg-white/5 backdrop-blur-lg">
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 rounded-3xl border border-border"
      />
      <div className="relative z-10 flex h-36 flex-col items-start justify-between px-4 pb-4 pt-6">
        <textarea
          value={question}
          onChange={(e) => onQuestionChange(e.target.value)}
          placeholder={t("home.analytics.placeholder")}
          rows={2}
          disabled={composerBusy}
          onKeyDown={(e: React.KeyboardEvent<HTMLTextAreaElement>) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              void onSend();
            }
          }}
          className="min-h-0 w-full flex-1 resize-none border-none bg-transparent text-base font-normal leading-5 text-foreground outline-none placeholder:text-muted"
        />
        <div className="flex w-full flex-wrap items-center justify-between gap-1">
          {dataSourcesLoaded && dataSources.length > 0 ? (
            <button
              type="button"
              disabled={composerBusy}
              onClick={onOpenSourceModal}
              title={t("home.figma.source")}
              aria-label={t("home.figma.source")}
              className="relative flex h-9 min-w-0 max-w-[min(260px,46vw)] shrink-0 cursor-pointer items-center gap-2 rounded-3xl border border-border bg-surface py-2 pl-3 pr-9 text-sm font-medium leading-5 text-foreground outline-none transition-colors hover:bg-surface-secondary disabled:cursor-not-allowed disabled:opacity-50"
            >
              <Icon icon="mdi:database-outline" width={16} className="shrink-0 text-muted" />
              <span className="min-w-0 flex-1 truncate text-left">{sourceButtonLabel}</span>
              <Icon
                icon="mdi:chevron-down"
                width={16}
                className="pointer-events-none absolute right-2.5 text-muted"
                aria-hidden
              />
            </button>
          ) : (
            <button
              type="button"
              disabled
              title={
                dataSourcesLoaded
                  ? t("home.figma.reportsSoon")
                  : t("home.figma.dataSourcesLoading")
              }
              className="flex h-9 shrink-0 cursor-not-allowed items-center gap-2 rounded-3xl bg-surface px-4 py-2 text-sm font-medium leading-5 text-foreground opacity-50 transition-all duration-200 ease-in-out"
            >
              <Icon icon="mdi:database-outline" width={16} />
              {dataSourcesLoaded ? t("home.figma.source") : t("home.figma.dataSourcesLoading")}
              <Icon icon="mdi:chevron-down" width={16} />
            </button>
          )}
          <div className="flex items-center gap-1">
            <button
              type="button"
              onClick={() => void onSend()}
              disabled={composerBusy || !question.trim() || !nlChatReady}
              className="flex h-9 shrink-0 cursor-pointer items-center gap-2 rounded-3xl bg-foreground px-4 py-2 text-sm font-medium leading-5 text-background transition-all duration-200 ease-in-out hover:bg-foreground/90 disabled:cursor-not-allowed disabled:opacity-50 active:scale-[0.97]"
            >
              {composerBusy ? (
                <>
                  <Icon icon="mdi:loading" className="animate-spin" width={18} />
                  {t("home.analytics.running")}
                </>
              ) : (
                <>
                  <Icon icon="mdi:send" width={18} />
                  {t("home.figma.send")}
                </>
              )}
            </button>
            <FigmaSimpleTooltip label={t("home.figma.voiceTooltip")} side="top">
              <button
                type="button"
                onClick={onVoiceOpen}
                className="relative flex size-9 cursor-pointer items-center justify-center rounded-3xl transition-colors hover:bg-surface/60 active:scale-[0.97]"
              >
                <Icon icon="mdi:microphone" className="text-foreground" width={18} />
                <span
                  aria-hidden="true"
                  className="pointer-events-none absolute inset-0 rounded-3xl border border-border"
                />
              </button>
            </FigmaSimpleTooltip>
          </div>
        </div>
      </div>
    </div>
  );
}
