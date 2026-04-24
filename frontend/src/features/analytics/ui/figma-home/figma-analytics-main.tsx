import {
  Profiler,
  useCallback,
  useState,
  type ProfilerOnRenderCallback,
  type ReactNode,
} from "react";
import { AnimatePresence } from "motion/react";
import { Icon } from "@iconify/react";
import { ScrollShadow } from "@heroui/react";

import type { AnalyticsDataSourceItem } from "../../api/analytics-api";
import type {
  ChatSuggestionTopic,
  FigmaTranslateFn,
} from "../../config/figma-analytics-faq";
import type { InterpretationHint } from "../../lib/interpretation-hint";
import type { NlChatLine } from "../../lib/use-nl-orchestrator-chat";
import {
  NlChatTranscriptBlock,
  type NlChatAssistantActionHandlers,
} from "../analytics-panel/nl-chat-transcript-block";

import { FigmaAnalyticsHero } from "./figma-analytics-hero";
import { FigmaChatHeaderRow } from "./figma-chat-header-row";
import { FigmaNlComposer } from "./figma-nl-composer";
import { FigmaSourceModal } from "./figma-source-modal";
import { FigmaSuggestionBlock } from "./figma-suggestion-block";
import { FigmaSimpleTooltip } from "./figma-simple-tooltip";
import { FIGMA_CHAT_COLUMN_MAX_PX } from "./figma-tokens";
import { FigmaVoiceStubPanel } from "./figma-voice-stub-panel";

const nlChatProfilerOnRender: ProfilerOnRenderCallback = (
  id,
  phase,
  actualDuration,
) => {
  if (actualDuration > 12) {
    console.debug(`[Profiler ${id}] ${phase} ${actualDuration.toFixed(1)}ms`);
  }
};

function wrapNlChatProfiler(children: ReactNode) {
  if (!import.meta.env.DEV) return children;
  if (
    typeof window === "undefined" ||
    window.localStorage.getItem("nlChatProfiler") !== "1"
  ) {
    return children;
  }
  return (
    <Profiler id="NlChatTranscript" onRender={nlChatProfilerOnRender}>
      {children}
    </Profiler>
  );
}

export type FigmaAnalyticsMainProps = {
  t: FigmaTranslateFn;
  sidebarOpen: boolean;
  onOpenSidebar: () => void;
  interpretationHint: InterpretationHint | null;
  hideInterpretationStrip: boolean;
  question: string;
  composerBusy: boolean;
  nlChatLines: NlChatLine[];
  nlChatReady: boolean;
  dataSources: AnalyticsDataSourceItem[];
  selectedSourceKey: string | null;
  selectedSourceLabel: string;
  onSourceKeyChange: (key: string) => void;
  dataSourcesLoaded: boolean;
  chatSuggestions: ChatSuggestionTopic[];
  chatSuggestionsLoaded: boolean;
  nlConversationId: string | null;
  nlChatAccessRole?: "owner" | "viewer" | null;
  cloneSharedBusy?: boolean;
  onShareChat: () => void;
  onCloneSharedChat?: () => void;
  historyBusy: boolean;
  onRefreshHistory: () => void;
  onQuestionChange: (v: string) => void;
  onSend: () => void;
  onStartNewChat: () => void;
  nlAssistantActionHandlers?: NlChatAssistantActionHandlers | null;
};

const chatColClass = "mx-auto w-full py-1 pb-4";
const chatColStyle = { maxWidth: FIGMA_CHAT_COLUMN_MAX_PX } as const;

export function FigmaAnalyticsMain({
  t,
  sidebarOpen,
  onOpenSidebar,
  interpretationHint: _interpretationHint,
  hideInterpretationStrip: _hideInterpretationStrip,
  question,
  composerBusy,
  nlChatLines,
  nlChatReady,
  dataSources,
  selectedSourceKey,
  selectedSourceLabel,
  onSourceKeyChange,
  dataSourcesLoaded,
  chatSuggestions,
  chatSuggestionsLoaded,
  nlConversationId,
  nlChatAccessRole = "owner",
  cloneSharedBusy = false,
  onShareChat,
  onCloneSharedChat,
  historyBusy,
  onRefreshHistory,
  onQuestionChange,
  onSend,
  onStartNewChat,
  nlAssistantActionHandlers,
}: FigmaAnalyticsMainProps) {
  const [voiceOpen, setVoiceOpen] = useState(false);
  const [sourceModalOpen, setSourceModalOpen] = useState(false);
  const [activeFaq, setActiveFaq] = useState<string | null>(null);
  const [scrollerEl, setScrollerEl] = useState<HTMLElement | null>(null);
  const hasChat = nlChatLines.length > 0;
  const showHero = !hasChat;
  const isNlViewer = nlChatAccessRole === "viewer";
  const showViewerCloneBar =
    isNlViewer && Boolean(nlConversationId) && Boolean(onCloneSharedChat);
  const sourceButtonLabel =
    selectedSourceLabel ||
    dataSources.find((s) => s.key === selectedSourceKey)?.display_name ||
    t("home.figma.source");

  const handleFaqPick = useCallback(
    (text: string) => {
      onQuestionChange(text);
    },
    [onQuestionChange],
  );

  const composer = (
    <FigmaNlComposer
      t={t}
      question={question}
      composerBusy={composerBusy}
      nlChatReady={nlChatReady}
      dataSourcesLoaded={dataSourcesLoaded}
      dataSources={dataSources}
      sourceButtonLabel={sourceButtonLabel}
      onOpenSourceModal={() => setSourceModalOpen(true)}
      onQuestionChange={onQuestionChange}
      onSend={onSend}
      onVoiceOpen={() => setVoiceOpen(true)}
    />
  );

  const viewerBottomBar =
    showViewerCloneBar && onCloneSharedChat ? (
      <div className="flex justify-center">
        <button
          type="button"
          disabled={!nlConversationId || cloneSharedBusy}
          onClick={() => void onCloneSharedChat()}
          className="inline-flex h-10 min-h-10 min-w-0 max-w-full cursor-pointer items-center justify-center gap-2 rounded-full bg-white px-6 font-sans text-[15px] font-medium text-black shadow-md shadow-black/30 transition-all duration-200 ease-in-out hover:enabled:bg-zinc-100 hover:enabled:shadow-lg active:enabled:scale-[0.97] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white/40 disabled:cursor-not-allowed disabled:opacity-50 с"
        >
          {cloneSharedBusy && (
            <Icon
              icon="mdi:loading"
              className="shrink-0 animate-spin text-black"
              width={20}
            />
          )}
          {cloneSharedBusy
            ? t("home.figma.cloneSharedWorking")
            : t("home.figma.viewerContinueCta")}
        </button>
      </div>
    ) : null;

  const bottomInput = showViewerCloneBar ? viewerBottomBar : composer;

  return (
    <div className="relative flex h-full min-h-0 w-full flex-1 flex-col">
      <div className="relative flex h-full min-h-0 w-full min-w-0 flex-1 flex-col overflow-hidden py-4 bg-[#060607] bg-[url(/mpit.png)] bg-cover bg-no-repeat">
        <div className="pointer-events-none absolute inset-0 h-full w-full bg-black opacity-30" />

        <div className="relative z-10 flex min-h-0 min-w-0 flex-1 flex-col">
          {/* Бургер-кнопка при свёрнутом сайдбаре — абсолютно позиционирована в левом верхнем углу */}
          {!sidebarOpen && (
            <div className="absolute top-5 left-5 z-10">
              <FigmaSimpleTooltip
                label={t("home.figma.openSidebar")}
                side="bottom"
              >
                <button
                  type="button"
                  onClick={onOpenSidebar}
                  className="flex size-10 shrink-0 cursor-pointer items-center justify-center rounded-[24px] transition-all hover:bg-[#27272a]/60 active:scale-[0.97]"
                >
                  <Icon icon="mdi:menu" className="text-[#fcfcfc]" width={22} />
                </button>
              </FigmaSimpleTooltip>
            </div>
          )}

          {hasChat ? (
            <div className="flex min-h-0 flex-1 flex-col overflow-hidden">
              <div className="shrink-0 px-5 pt-5">
                <FigmaChatHeaderRow
                  t={t}
                  nlConversationId={nlConversationId}
                  nlChatAccessRole={nlChatAccessRole}
                  onShareChat={onShareChat}
                  historyBusy={historyBusy}
                  onRefreshHistory={onRefreshHistory}
                  onStartNewChat={onStartNewChat}
                />
              </div>
              <div className="flex min-h-0 flex-1 flex-col overflow-hidden">
                {/* Плашка «ясность формулировки» — временно скрыта */}
                <ScrollShadow
                  ref={(el) => setScrollerEl(el as HTMLElement | null)}
                  className="min-h-0 flex-1 max-h-[calc(100vh-240px)] overscroll-y-contain px-3 sm:px-5"
                  hideScrollBar
                >
                  <div className={chatColClass} style={chatColStyle}>
                    {wrapNlChatProfiler(
                      <NlChatTranscriptBlock
                        t={t}
                        nlChatLines={nlChatLines}
                        variant="grok"
                        emptyLabel={t("home.analytics.chatEmpty")}
                        assistantActionHandlers={
                          nlAssistantActionHandlers ?? null
                        }
                        assistantActionsLocked={composerBusy || isNlViewer}
                        scrollerEl={scrollerEl}
                        nlConversationId={nlConversationId}
                      />,
                    )}
                  </div>
                </ScrollShadow>
              </div>
              <div className="shrink-0 px-5 pb-4 pt-3">
                <div className="mx-auto w-full" style={chatColStyle}>
                  {bottomInput}
                </div>
              </div>
            </div>
          ) : (
            <div className="relative flex min-h-0 flex-1 flex-col overflow-y-auto">
              <div className="relative flex w-full h-full flex-col gap-10 p-5 pb-10 items-center justify-center">
                <FigmaChatHeaderRow
                  t={t}
                  nlConversationId={nlConversationId}
                  nlChatAccessRole={nlChatAccessRole}
                  onShareChat={onShareChat}
                  historyBusy={historyBusy}
                  onRefreshHistory={onRefreshHistory}
                  onStartNewChat={onStartNewChat}
                />
                {showHero && <FigmaAnalyticsHero t={t} />}
                <div className="flex w-full flex-col gap-4">
                  <div
                    className="flex flex-col mx-auto w-full gap-6"
                    style={chatColStyle}
                  >
                    {bottomInput}
                    {showHero && !isNlViewer && (
                      <FigmaSuggestionBlock
                        t={t}
                        activeFaq={activeFaq}
                        setActiveFaq={setActiveFaq}
                        apiTopics={chatSuggestions}
                        apiLoaded={chatSuggestionsLoaded}
                        onPick={handleFaqPick}
                      />
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
      <AnimatePresence>
        {sourceModalOpen && (
          <FigmaSourceModal
            t={t}
            open={sourceModalOpen}
            sources={dataSources}
            selectedKey={selectedSourceKey ?? dataSources[0]?.key ?? null}
            onClose={() => setSourceModalOpen(false)}
            onApply={(key) => onSourceKeyChange(key)}
          />
        )}
      </AnimatePresence>
      <AnimatePresence>
        {voiceOpen && (
          <FigmaVoiceStubPanel t={t} onClose={() => setVoiceOpen(false)} />
        )}
      </AnimatePresence>
    </div>
  );
}

