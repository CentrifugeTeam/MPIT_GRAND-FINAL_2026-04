import { useCallback, useState } from "react";
import { AnimatePresence } from "motion/react";

import type { AnalyticsDataSourceItem } from "@/features/analytics/api/analytics-api";
import type {
  FigmaFaqId,
  FigmaTranslateFn,
} from "@/features/analytics/config/figma-analytics-faq";
import type { InterpretationHint } from "@/features/analytics/lib/interpretation-hint";
import type { NlChatLine } from "@/features/analytics/lib/use-nl-orchestrator-chat";
import { NlChatTranscriptBlock } from "@/features/analytics/ui/analytics-panel/nl-chat-transcript-block";

import { FigmaAnalyticsHero } from "./figma-analytics-hero";
import { FigmaChatHeaderRow } from "./figma-chat-header-row";
import { FigmaNlComposer } from "./figma-nl-composer";
import { FigmaSourceModal } from "./figma-source-modal";
import { FigmaSuggestionBlock } from "./figma-suggestion-block";
import { FIGMA_CHAT_COLUMN_MAX_PX } from "./figma-tokens";
import { FigmaVoiceStubPanel } from "./figma-voice-stub-panel";

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
  nlConversationId: string | null;
  onShareChat: () => void;
  historyBusy: boolean;
  onRefreshHistory: () => void;
  onQuestionChange: (v: string) => void;
  onSend: () => void;
  onStartNewChat: () => void;
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
  nlConversationId,
  onShareChat,
  historyBusy,
  onRefreshHistory,
  onQuestionChange,
  onSend,
  onStartNewChat,
}: FigmaAnalyticsMainProps) {
  const [voiceOpen, setVoiceOpen] = useState(false);
  const [sourceModalOpen, setSourceModalOpen] = useState(false);
  const [activeFaq, setActiveFaq] = useState<FigmaFaqId | null>(null);
  const hasChat = nlChatLines.length > 0;
  const showHero = !hasChat;
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

  return (
    <div className="relative flex h-full min-h-0 w-full flex-1 flex-col">
      <div className="relative flex h-full min-h-0 w-full min-w-0 flex-1 flex-col overflow-hidden rounded-2xl border border-solid border-[#28282c] bg-[#060607]">
        {hasChat ? (
          <div className="flex min-h-0 flex-1 flex-col overflow-hidden">
            <div className="shrink-0 px-5 pt-5">
              <FigmaChatHeaderRow
                t={t}
                sidebarOpen={sidebarOpen}
                onOpenSidebar={onOpenSidebar}
                nlConversationId={nlConversationId}
                onShareChat={onShareChat}
                historyBusy={historyBusy}
                onRefreshHistory={onRefreshHistory}
                onStartNewChat={onStartNewChat}
              />
            </div>
            <div className="flex min-h-0 flex-1 flex-col overflow-hidden">
              {/* Плашка «ясность формулировки» — временно скрыта */}
              <div className="min-h-0 flex-1 max-h-[calc(100vh-240px)] overflow-y-auto overscroll-y-contain px-3 sm:px-5">
                <div className={chatColClass} style={chatColStyle}>
                  <NlChatTranscriptBlock
                    t={t}
                    nlChatLines={nlChatLines}
                    variant="grok"
                    emptyLabel={t("home.analytics.chatEmpty")}
                  />
                </div>
              </div>
            </div>
            <div className="shrink-0 bg-[#060607] px-5 pb-4 pt-3">
              <div className="mx-auto w-full" style={chatColStyle}>
                {composer}
              </div>
            </div>
          </div>
        ) : (
          <div className="relative flex min-h-0 flex-1 flex-col overflow-y-auto">
            <div className="flex w-full flex-col gap-10 p-5 pb-10">
              <FigmaChatHeaderRow
                t={t}
                sidebarOpen={sidebarOpen}
                onOpenSidebar={onOpenSidebar}
                nlConversationId={nlConversationId}
                onShareChat={onShareChat}
                historyBusy={historyBusy}
                onRefreshHistory={onRefreshHistory}
                onStartNewChat={onStartNewChat}
              />
              {showHero && <FigmaAnalyticsHero t={t} />}
              <div className="flex w-full flex-col gap-4">
                <div className="mx-auto w-full" style={chatColStyle}>
                  {composer}
                </div>
                {showHero && (
                  <FigmaSuggestionBlock
                    t={t}
                    activeFaq={activeFaq}
                    setActiveFaq={setActiveFaq}
                    onPick={handleFaqPick}
                  />
                )}
              </div>
            </div>
          </div>
        )}
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
        {voiceOpen && <FigmaVoiceStubPanel t={t} onClose={() => setVoiceOpen(false)} />}
      </AnimatePresence>
    </div>
  );
}
