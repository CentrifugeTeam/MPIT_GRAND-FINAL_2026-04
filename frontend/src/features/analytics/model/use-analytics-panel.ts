import { useCallback, useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';

import type { ChartPayloadShape, NlSqlWsPayload } from '@/entities/analytics';
import {
  useAnalyticsChatStore,
  useAnalyticsChatTitlesStore,
  useAnalyticsHistory,
} from '@/features/analytics-history';
import { useAnalyticsRenameRow } from '@/features/analytics-rename';
import { useAnalyticsDataSources } from '@/features/analytics-sources';
import {
  useAnalyticsSendMessage,
  useNlOrchestratorChat,
} from '@/features/analytics-chat';
import { fetchNlChatSessionMeta } from '@/features/analytics/api/analytics-api';
import { useWsStore } from '@/shared/lib/ws-store';

import type { InterpretationHint } from '../lib/interpretation-hint';
import { useChatSuggestions } from './use-chat-suggestions';

type UseAnalyticsPanelOptions = {
  initialConversationId?: string | null;
};

export function useAnalyticsPanel(options?: UseAnalyticsPanelOptions) {
  const initialConversationId = options?.initialConversationId?.trim() || null;
  const { t } = useTranslation();
  const [nlConversationId, setNlConversationId] =
    useState<string | null>(initialConversationId);
  const entries = useAnalyticsChatStore(s => s.entries);
  const activeId = useAnalyticsChatStore(s => s.activeId);
  const setActive = useAnalyticsChatStore(s => s.setActive);
  const titles = useAnalyticsChatTitlesStore(s => s.titles);

  const [question, setQuestion] = useState('');
  const [maxRowsStr, setMaxRowsStr] = useState('');
  const [result, setResult] = useState<NlSqlWsPayload | null>(null);
  const [interpretationHint, setInterpretationHint] =
    useState<InterpretationHint | null>(null);
  const disconnectWs = useWsStore(s => s.disconnect);
  const [preferDraftNl, setPreferDraftNl] = useState(() => initialConversationId == null);
  const [nlChatAccessRole, setNlChatAccessRole] = useState<'owner' | 'viewer'>('owner');

  useEffect(() => {
    if (initialConversationId == null) return;
    setPreferDraftNl(false);
    setNlConversationId(initialConversationId);
    setActive(null);
    setQuestion('');
    setMaxRowsStr('');
    setResult(null);
    setInterpretationHint(null);
  }, [initialConversationId, setActive]);

  useEffect(() => {
    if (!nlConversationId) {
      setNlChatAccessRole('owner');
      return;
    }
    let cancelled = false;
    void fetchNlChatSessionMeta(nlConversationId)
      .then(meta => {
        if (!cancelled) setNlChatAccessRole(meta.access_role);
      })
      .catch(() => {
        if (!cancelled) setNlChatAccessRole('owner');
      });
    return () => {
      cancelled = true;
    };
  }, [nlConversationId]);

  const {
    lines: nlChatLines,
    nlChatBusy,
    sendChat,
    trimForRetry,
    requestDeleteChatMessages,
    getRetryTailAnchorId,
    requestDeleteChatTailFrom,
  } = useNlOrchestratorChat(t, nlConversationId, nlChatAccessRole === 'viewer');

  const {
    dataSources,
    selectedSourceKey,
    setSelectedSourceKey,
    dataSourcesLoaded,
    selectedSourceLabel,
    nlChatReady,
  } = useAnalyticsDataSources();

  const {
    editingRowId,
    renameDraft,
    renameFieldFocused,
    renameInputRef,
    setRenameDraft,
    setRenameFieldFocused,
    startEditingRow,
    cancelRename,
    commitRename,
  } = useAnalyticsRenameRow();

  const {
    historyBusy,
    loadHistory,
    selectEntry,
    deleteHistoryEntry,
    clearAllHistoryEntries,
  } = useAnalyticsHistory({
    activeId,
    nlConversationId,
    preferDraftNl,
    setNlConversationId,
    setQuestion,
    setMaxRowsStr,
    setResult,
    setInterpretationHint,
    setPreferDraftNl,
  });

  useEffect(() => {
    return () => {
      disconnectWs();
    };
  }, [disconnectWs]);

  const startNewChat = useCallback(() => {
    setPreferDraftNl(true);
    setActive(null);
    setNlConversationId(null);
    setNlChatAccessRole('owner');
    setQuestion('');
    setMaxRowsStr('');
    setResult(null);
    setInterpretationHint(null);
  }, [setActive]);

  const { sendComposerMessage, sendMessageWithText, interpretBusy } =
    useAnalyticsSendMessage({
      question,
      setQuestion,
      nlChatBusy,
      nlConversationId,
      setNlConversationId,
      setPreferDraftNl,
      setActive,
      loadHistory,
      dataSourcesLoaded,
      dataSourcesLength: dataSources.length,
      selectedSourceKey,
      selectedSourceLabel,
      sendChat,
      setInterpretationHint,
      maxRowsStr,
      nlReadOnly: nlChatAccessRole === 'viewer',
    });

  const chartPayload = result?.chart_payload;
  const showChart = useMemo(() => {
    const cp = chartPayload as ChartPayloadShape | undefined;
    return Boolean(
      cp &&
      (cp.type === 'bar' || cp.type === 'line') &&
      (cp.labels?.length ?? 0) > 0 &&
      (cp.series?.length ?? 0) > 0,
    );
  }, [chartPayload]);

  const composerBusy = nlChatBusy || interpretBusy;
  const chatSuggestionsQuery = useChatSuggestions(selectedSourceKey);

  return {
    t,
    entries,
    titles,
    activeId,
    editingRowId,
    renameDraft,
    renameFieldFocused,
    renameInputRef,
    historyBusy,
    setRenameDraft,
    setRenameFieldFocused,
    commitRename,
    cancelRename,
    selectEntry,
    startNewChat,
    loadHistory,
    clearAllHistoryEntries,
    deleteHistoryEntry,
    startEditingRow,
    question,
    setQuestion,
    maxRowsStr,
    setMaxRowsStr,
    composerBusy,
    sendComposerMessage,
    sendMessageWithText,
    result,
    showChart,
    chartPayload,
    interpretationHint,
    nlChatLines,
    trimForRetry,
    requestDeleteChatMessages,
    getRetryTailAnchorId,
    requestDeleteChatTailFrom,
    nlConversationId,
    nlChatAccessRole,
    nlChatReady,
    dataSources,
    selectedSourceKey,
    selectedSourceLabel,
    setSelectedSourceKey,
    dataSourcesLoaded,
    chatSuggestions: chatSuggestionsQuery.data?.items ?? [],
    chatSuggestionsLoaded: chatSuggestionsQuery.isFetched,
  };
}
