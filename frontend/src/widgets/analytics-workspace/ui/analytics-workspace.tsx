import { useCallback, useEffect, useRef, useState } from 'react';
import { useNavigate, useParams } from 'react-router';

import {
  AnalyticsResults,
  FigmaAnalyticsMain,
  FigmaAnalyticsSidebar,
  useAnalyticsPanel,
} from '@/features/analytics';

export function AnalyticsWorkspace() {
  const { id: routeChatId } = useParams<{ id?: string }>();
  const p = useAnalyticsPanel({ initialConversationId: routeChatId ?? null });
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const navigate = useNavigate();

  const { entries, historyBusy, selectEntry } = p;

  // Navigate to /home/:id when a new conversation is first created
  const navigatedConvRef = useRef<string | null>(null);
  useEffect(() => {
    if (
      p.nlConversationId &&
      !routeChatId &&
      navigatedConvRef.current !== p.nlConversationId
    ) {
      navigatedConvRef.current = p.nlConversationId;
      void navigate(`/home/${p.nlConversationId}`, { replace: true });
    }
    if (!p.nlConversationId) {
      navigatedConvRef.current = null;
    }
  }, [p.nlConversationId, routeChatId, navigate]);

  useEffect(() => {
    if (historyBusy) return;
    const cid = routeChatId?.trim();
    if (!cid) return;
    const matched = entries.find(e => (e.conversationId ?? e.id) === cid);
    if (matched) selectEntry(matched.id);
  }, [entries, historyBusy, routeChatId, selectEntry]);

  const nlAssistantActionHandlers = {
    /** Локально обрезает ленту; при перезагрузке чата сообщения снова придут с сервера. */
    onRetry: ({
      assistantLineId,
      userMessage,
    }: {
      assistantLineId: string;
      userMessage: string;
      userLineId: string | null;
    }) => {
      const anchor =
        p.getRetryTailAnchorId(assistantLineId) ?? assistantLineId;
      p.trimForRetry(assistantLineId);
      void p.requestDeleteChatTailFrom(anchor);
      p.setQuestion(userMessage);
      queueMicrotask(() => {
        void p.sendComposerMessage();
      });
    },
    onCreateReportTask: (userQuestion: string) => {
      void navigate('/reports', {
        state: { createReportFromChat: { instruction: userQuestion } },
      });
    },
  } as const;

  const handleShareChat = useCallback(async () => {
    if (!p.nlConversationId) return;
    const u = new URL(window.location.href);
    u.pathname = `/home/${p.nlConversationId}`;
    u.search = '';
    try {
      await navigator.clipboard.writeText(u.toString());
    } catch {
      /* ignore */
    }
  }, [p.nlConversationId]);

  return (
    <div className='flex min-h-0 w-full flex-1 items-stretch gap-4 overflow-hidden bg-background pl-0'>
      <div className='flex min-h-0 shrink-0 self-stretch'>
        <FigmaAnalyticsSidebar
          isOpen={sidebarOpen}
          onToggle={() => setSidebarOpen(v => !v)}
          entries={p.entries}
          titles={p.titles}
          activeId={p.activeId}
          editingRowId={p.editingRowId}
          renameDraft={p.renameDraft}
          renameFieldFocused={p.renameFieldFocused}
          renameInputRef={p.renameInputRef}
          historyBusy={p.historyBusy}
          onRenameDraft={p.setRenameDraft}
          onRenameFocus={p.setRenameFieldFocused}
          onCommitRename={p.commitRename}
          onCancelRename={p.cancelRename}
          onSelectEntry={entryId => {
            const entry = p.entries.find(e => e.id === entryId);
            const chatId = entry?.conversationId;
            if (chatId) {
              void navigate(`/home/${chatId}`);
              return;
            }
            p.selectEntry(entryId);
          }}
          onStartNewChat={() => {
            p.startNewChat();
            void navigate('/home');
          }}
          onLoadHistory={() => void p.loadHistory()}
          onClearAllHistory={() => void p.clearAllHistoryEntries()}
          onStartEditingRow={p.startEditingRow}
          onDeleteHistoryEntry={id => void p.deleteHistoryEntry(id)}
          t={p.t}
        />
      </div>

      <div className='flex min-h-0 min-w-0 flex-1 flex-col'>
        <FigmaAnalyticsMain
          t={p.t}
          sidebarOpen={sidebarOpen}
          onOpenSidebar={() => setSidebarOpen(true)}
          interpretationHint={p.interpretationHint}
          hideInterpretationStrip={!!p.result}
          question={p.question}
          composerBusy={p.composerBusy}
          nlChatLines={p.nlChatLines}
          nlChatReady={p.nlChatReady}
          dataSources={p.dataSources}
          selectedSourceKey={p.selectedSourceKey}
          selectedSourceLabel={p.selectedSourceLabel}
          onSourceKeyChange={p.setSelectedSourceKey}
          dataSourcesLoaded={p.dataSourcesLoaded}
          nlConversationId={p.nlConversationId}
          onShareChat={handleShareChat}
          historyBusy={p.historyBusy}
          onRefreshHistory={() => void p.loadHistory()}
          onQuestionChange={p.setQuestion}
          onSend={() => void p.sendComposerMessage()}
          onStartNewChat={() => {
            p.startNewChat();
            void navigate('/home');
          }}
          nlAssistantActionHandlers={nlAssistantActionHandlers}
        />

        {p.result && (
          <div className='shrink-0 border-t border-border'>
            <div className='max-h-[min(45vh,520px)] w-full overflow-y-auto px-5 py-4'>
              <AnalyticsResults
                t={p.t}
                result={p.result}
                showChart={p.showChart}
                chartPayload={p.chartPayload}
                interpretationFallback={p.interpretationHint}
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
