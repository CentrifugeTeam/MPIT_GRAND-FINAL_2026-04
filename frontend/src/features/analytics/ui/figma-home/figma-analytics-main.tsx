import { useCallback, useState } from 'react';
import { AnimatePresence } from 'motion/react';
import { Icon } from '@iconify/react';
import { ScrollShadow } from '@heroui/react';

import type { AnalyticsDataSourceItem } from '../../api/analytics-api';
import type {
  ChatSuggestionTopic,
  FigmaTranslateFn,
} from '../../config/figma-analytics-faq';
import type { InterpretationHint } from '../../lib/interpretation-hint';
import type { NlChatLine } from '../../lib/use-nl-orchestrator-chat';
import {
  NlChatTranscriptBlock,
  type NlChatAssistantActionHandlers,
} from '../analytics-panel/nl-chat-transcript-block';

import { FigmaAnalyticsHero } from './figma-analytics-hero';
import { FigmaChatHeaderRow } from './figma-chat-header-row';
import { FigmaNlComposer } from './figma-nl-composer';
import { FigmaSourceModal } from './figma-source-modal';
import { FigmaSuggestionBlock } from './figma-suggestion-block';
import { FigmaSimpleTooltip } from './figma-simple-tooltip';
import { FIGMA_CHAT_COLUMN_MAX_PX } from './figma-tokens';
import { FigmaVoiceStubPanel } from './figma-voice-stub-panel';

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
  onShareChat: () => void;
  historyBusy: boolean;
  onRefreshHistory: () => void;
  onQuestionChange: (v: string) => void;
  onSend: () => void;
  onStartNewChat: () => void;
  nlAssistantActionHandlers?: NlChatAssistantActionHandlers | null;
};

const chatColClass = 'mx-auto w-full py-1 pb-4';
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
  onShareChat,
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
  const sourceButtonLabel =
    selectedSourceLabel ||
    dataSources.find(s => s.key === selectedSourceKey)?.display_name ||
    t('home.figma.source');

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
    <div className='relative flex h-full min-h-0 w-full flex-1 flex-col'>
      <div className='relative flex h-full min-h-0 w-full min-w-0 flex-1 flex-col overflow-hidden py-4 bg-[#060607] bg-[url(/mpit.png)] bg-cover bg-no-repeat'>
        <div className='w-full h-full opacity-30 absolute inset-0 bg-black pointer-events-none' />

        {/* Бургер-кнопка при свёрнутом сайдбаре — абсолютно позиционирована в левом верхнем углу */}
        {!sidebarOpen && (
          <div className='absolute top-5 left-5 z-10'>
            <FigmaSimpleTooltip
              label={t('home.figma.openSidebar')}
              side='bottom'
            >
              <button
                type='button'
                onClick={onOpenSidebar}
                className='flex size-10 shrink-0 cursor-pointer items-center justify-center rounded-[24px] transition-all hover:bg-[#27272a]/60 active:scale-[0.97]'
              >
                <Icon
                  icon='mdi:menu'
                  className='text-[#fcfcfc]'
                  width={22}
                />
              </button>
            </FigmaSimpleTooltip>
          </div>
        )}

        {hasChat ? (
          <div className='flex min-h-0 flex-1 flex-col overflow-hidden'>
            <div className='shrink-0 px-5 pt-5'>
              <FigmaChatHeaderRow
                t={t}
                nlConversationId={nlConversationId}
                onShareChat={onShareChat}
                historyBusy={historyBusy}
                onRefreshHistory={onRefreshHistory}
                onStartNewChat={onStartNewChat}
              />
            </div>
            <div className='flex min-h-0 flex-1 flex-col overflow-hidden'>
              {/* Плашка «ясность формулировки» — временно скрыта */}
              <ScrollShadow
                ref={(el) => setScrollerEl(el as HTMLElement | null)}
                className='min-h-0 flex-1 max-h-[calc(100vh-240px)] overscroll-y-contain px-3 sm:px-5'
                hideScrollBar
              >
                <div
                  className={chatColClass}
                  style={chatColStyle}
                >
                  <NlChatTranscriptBlock
                    t={t}
                    nlChatLines={nlChatLines}
                    variant='grok'
                    emptyLabel={t('home.analytics.chatEmpty')}
                    assistantActionHandlers={nlAssistantActionHandlers ?? null}
                    assistantActionsLocked={composerBusy}
                    scrollerEl={scrollerEl}
                  />
                </div>
              </ScrollShadow>
            </div>
            <div className='shrink-0 px-5 pb-4 pt-3'>
              <div
                className='mx-auto w-full'
                style={chatColStyle}
              >
                {composer}
              </div>
            </div>
          </div>
        ) : (
          <div className='relative flex min-h-0 flex-1 flex-col overflow-y-auto'>
            <div className='relative flex w-full h-full flex-col gap-10 p-5 pb-10 items-center justify-center'>
              <FigmaChatHeaderRow
                t={t}
                nlConversationId={nlConversationId}
                onShareChat={onShareChat}
                historyBusy={historyBusy}
                onRefreshHistory={onRefreshHistory}
                onStartNewChat={onStartNewChat}
              />
              {showHero && <FigmaAnalyticsHero t={t} />}
              <div className='flex w-full flex-col gap-4'>
                <div
                  className='flex flex-col mx-auto w-full gap-6'
                  style={chatColStyle}
                >
                  {composer}
                  {showHero && (
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
      <AnimatePresence>
        {sourceModalOpen && (
          <FigmaSourceModal
            t={t}
            open={sourceModalOpen}
            sources={dataSources}
            selectedKey={selectedSourceKey ?? dataSources[0]?.key ?? null}
            onClose={() => setSourceModalOpen(false)}
            onApply={key => onSourceKeyChange(key)}
          />
        )}
      </AnimatePresence>
      <AnimatePresence>
        {voiceOpen && (
          <FigmaVoiceStubPanel
            t={t}
            onClose={() => setVoiceOpen(false)}
          />
        )}
      </AnimatePresence>
    </div>
  );
}
