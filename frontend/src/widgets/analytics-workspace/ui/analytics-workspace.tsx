import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { AnimatePresence } from "motion/react";
import { useNavigate, useParams } from "react-router";
import { useQueryClient } from "@tanstack/react-query";

import {
  AnalyticsResults,
  answerChatInvite,
  cloneSharedChat,
  createShareChatInvites,
  FigmaAnalyticsMain,
  FigmaAnalyticsSidebar,
  FigmaChatInviteNotificationModal,
  FigmaShareAccessModal,
  CHAT_INVITES_QUERY_KEY,
  useAnalyticsPanel,
} from "@/features/analytics";
import {
  deleteNotification,
  type AppNotification,
} from '@/shared/api/notifications-api';
import { useAuthStore } from '@/shared/lib/auth-store';
import { forceReconnectNotificationSse } from '@/shared/lib/notification-sse-broadcast';

export function AnalyticsWorkspace() {
  const { id: routeChatId } = useParams<{ id?: string }>();
  const p = useAnalyticsPanel({ initialConversationId: routeChatId ?? null });
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const userUuid = useAuthStore(s => s.userUuid);

  const {
    entries,
    historyBusy,
    selectEntry,
    loadHistory,
    nlConversationId,
    getRetryTailAnchorId,
    trimForRetry,
    requestDeleteChatTailFrom,
    setQuestion,
    sendComposerMessage,
  } = p;
  const [shareModalOpen, setShareModalOpen] = useState(false);
  const [inviteNotif, setInviteNotif] = useState<AppNotification | null>(null);
  const [cloneSharedBusy, setCloneSharedBusy] = useState(false);

  const handleInviteModalAccept = useCallback(
    async (inviteId: string, notificationId: string) => {
      const res = await answerChatInvite(inviteId, 'accept');
      if (userUuid) {
        try {
          await deleteNotification(userUuid, notificationId);
        } catch {
          /* ignore */
        }
      }
      forceReconnectNotificationSse();
      await queryClient.invalidateQueries({ queryKey: CHAT_INVITES_QUERY_KEY });
      await loadHistory();
      if (res.conversation_id) {
        void navigate(`/home/${res.conversation_id}`);
      }
    },
    [navigate, loadHistory, queryClient, userUuid],
  );

  const handleInviteModalReject = useCallback(
    async (inviteId: string, notificationId: string) => {
      await answerChatInvite(inviteId, 'reject');
      if (userUuid) {
        try {
          await deleteNotification(userUuid, notificationId);
        } catch {
          /* ignore */
        }
      }
      forceReconnectNotificationSse();
      await queryClient.invalidateQueries({ queryKey: CHAT_INVITES_QUERY_KEY });
    },
    [queryClient, userUuid],
  );

  const handleShareEmailsSubmit = useCallback(
    async (emails: string[]) => {
      const cid = nlConversationId;
      if (!cid) return;
      await createShareChatInvites(cid, emails);
      await loadHistory();
    },
    [nlConversationId, loadHistory],
  );

  const handleCloneSharedChat = useCallback(async () => {
    const cid = nlConversationId;
    if (!cid) return;
    setCloneSharedBusy(true);
    try {
      const newId = await cloneSharedChat(cid);
      await loadHistory();
      void navigate(`/home/${newId}`);
    } finally {
      setCloneSharedBusy(false);
    }
  }, [nlConversationId, loadHistory, navigate]);

  // Navigate to /home/:id when a new conversation is first created
  const navigatedConvRef = useRef<string | null>(null);
  useEffect(() => {
    if (
      nlConversationId &&
      !routeChatId &&
      navigatedConvRef.current !== nlConversationId
    ) {
      navigatedConvRef.current = nlConversationId;
      void navigate(`/home/${nlConversationId}`, { replace: true });
    }
    if (!nlConversationId) {
      navigatedConvRef.current = null;
    }
  }, [nlConversationId, routeChatId, navigate]);

  useEffect(() => {
    if (historyBusy) return;
    const cid = routeChatId?.trim();
    if (!cid) return;
    const matched = entries.find(e => (e.conversationId ?? e.id) === cid);
    if (matched) selectEntry(matched.id);
  }, [entries, historyBusy, routeChatId, selectEntry]);

  const onRetry = useCallback(
    ({
      assistantLineId,
      userMessage,
    }: {
      assistantLineId: string;
      userMessage: string;
      userLineId: string | null;
    }) => {
      const anchor =
        getRetryTailAnchorId(assistantLineId) ?? assistantLineId;
      trimForRetry(assistantLineId);
      void requestDeleteChatTailFrom(anchor);
      setQuestion(userMessage);
      queueMicrotask(() => {
        void sendComposerMessage();
      });
    },
    [
      getRetryTailAnchorId,
      trimForRetry,
      requestDeleteChatTailFrom,
      setQuestion,
      sendComposerMessage,
    ],
  );

  const onCreateReportTask = useCallback(
    (userQuestion: string) => {
      void navigate('/reports', {
        state: { createReportFromChat: { instruction: userQuestion } },
      });
    },
    [navigate],
  );

  const nlAssistantActionHandlers = useMemo(
    () => ({ onRetry, onCreateReportTask }),
    [onRetry, onCreateReportTask],
  );

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
          onChatInviteNotification={n => setInviteNotif(n)}
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
          chatSuggestions={p.chatSuggestions}
          chatSuggestionsLoaded={p.chatSuggestionsLoaded}
          nlConversationId={nlConversationId}
          nlChatAccessRole={p.nlChatAccessRole}
          cloneSharedBusy={cloneSharedBusy}
          onShareChat={() => setShareModalOpen(true)}
          onCloneSharedChat={handleCloneSharedChat}
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

      <AnimatePresence>
        {shareModalOpen && nlConversationId ? (
          <FigmaShareAccessModal
            key='share-access'
            t={p.t}
            open
            onClose={() => setShareModalOpen(false)}
            onConfirm={({ emails }) => handleShareEmailsSubmit(emails)}
          />
        ) : null}
      </AnimatePresence>

      <AnimatePresence>
        {inviteNotif ? (
          <FigmaChatInviteNotificationModal
            key={inviteNotif.id}
            t={p.t}
            notification={inviteNotif}
            onClose={() => setInviteNotif(null)}
            onAccept={handleInviteModalAccept}
            onReject={handleInviteModalReject}
          />
        ) : null}
      </AnimatePresence>
    </div>
  );
}
