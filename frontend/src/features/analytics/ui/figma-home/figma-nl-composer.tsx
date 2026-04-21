import { Icon } from "@iconify/react";

import type { AnalyticsDataSourceItem } from "@/features/analytics/api/analytics-api";
import type { FigmaTranslateFn } from "@/features/analytics/config/figma-analytics-faq";
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
    <div className="relative w-full shrink-0 rounded-[24px] bg-[rgba(255,255,255,0.05)] backdrop-blur-[16px]">
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 rounded-[24px] border border-solid border-[#28282c]"
      />
      <div className="relative z-10 flex h-[139px] flex-col items-start justify-between px-[16px] pb-[16px] pt-[24px]">
        <textarea
          value={question}
          onChange={(e) => onQuestionChange(e.target.value)}
          placeholder={t("home.analytics.placeholder")}
          rows={2}
          disabled={composerBusy}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              void onSend();
            }
          }}
          className="min-h-0 w-full flex-1 resize-none border-none bg-transparent font-sans text-[16px] font-normal leading-5 text-[#fcfcfc] outline-none placeholder:text-[#a1a1aa]"
        />
        <div className="flex w-full flex-wrap items-center justify-between gap-1">
          {dataSourcesLoaded && dataSources.length > 0 ? (
            <button
              type="button"
              disabled={composerBusy}
              onClick={onOpenSourceModal}
              title={t("home.figma.source")}
              aria-label={t("home.figma.source")}
              className="relative flex h-9 min-w-0 max-w-[min(260px,46vw)] shrink-0 cursor-pointer items-center gap-2 rounded-[24px] border border-solid border-[#28282c] bg-[#27272a] py-2 pl-3 pr-9 font-sans text-[14px] font-medium leading-5 text-[#fcfcfc] outline-none transition-colors hover:bg-[#323236] disabled:cursor-not-allowed disabled:opacity-50"
            >
              <Icon icon="mdi:database-outline" width={16} className="shrink-0 text-[#a1a1aa]" />
              <span className="min-w-0 flex-1 truncate text-left">{sourceButtonLabel}</span>
              <Icon
                icon="mdi:chevron-down"
                width={16}
                className="pointer-events-none absolute right-2.5 text-[#a1a1aa]"
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
              className="flex h-9 shrink-0 cursor-not-allowed items-center gap-2 rounded-[24px] bg-[#27272a] px-4 py-2 font-sans text-[14px] font-medium leading-5 text-[#fcfcfc] opacity-50 transition-all duration-[250ms] ease-in-out"
            >
              <Icon icon="mdi:database-outline" width={16} />
              {dataSourcesLoaded ? t("home.figma.source") : t("home.figma.dataSourcesLoading")}
              <Icon icon="mdi:chevron-down" width={16} />
            </button>
          )}
          <div className="flex items-center gap-[4px]">
            <button
              type="button"
              onClick={() => void onSend()}
              disabled={composerBusy || !question.trim() || !nlChatReady}
              className="flex h-9 shrink-0 cursor-pointer items-center gap-2 rounded-[24px] bg-[#fcfcfc] px-4 py-2 font-sans text-[14px] font-medium leading-5 text-[#18181b] transition-all duration-[250ms] ease-in-out hover:bg-[#e4e4e7] disabled:cursor-not-allowed disabled:opacity-50 active:scale-[0.97]"
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
                className="relative flex size-9 cursor-pointer items-center justify-center rounded-[24px] transition-colors hover:bg-[#27272a]/60 active:scale-[0.97]"
              >
                <Icon icon="mdi:microphone" className="text-[#fcfcfc]" width={18} />
                <span
                  aria-hidden="true"
                  className="pointer-events-none absolute inset-0 rounded-[24px] border border-solid border-[#28282c]"
                />
              </button>
            </FigmaSimpleTooltip>
          </div>
        </div>
      </div>
    </div>
  );
}
