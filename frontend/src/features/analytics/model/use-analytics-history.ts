import { useCallback, useEffect, useState } from "react";

import {
  deleteAllAnalyticsHistory,
  deleteAnalyticsJob,
  deleteNlChat,
  fetchAnalyticsHistory,
} from "@/features/analytics/api/analytics-api";
import type { NlSqlWsPayload } from "@/entities/analytics";
import { historyItemToChatEntry } from "@/features/analytics/lib/history-mapper";
import {
  useAnalyticsChatStore,
  type AnalyticsChatEntry,
} from "@/features/analytics/model/analytics-chat-store";
import { useAnalyticsChatTitlesStore } from "@/features/analytics/model/analytics-chat-titles-store";
import {
  interpretationToHint,
  type InterpretationHint,
} from "@/features/analytics/lib/interpretation-hint";

type Args = {
  activeId: string | null;
  nlConversationId: string | null;
  preferDraftNl: boolean;
  setNlConversationId: (id: string | null) => void;
  setQuestion: (q: string) => void;
  setMaxRowsStr: (v: string) => void;
  setResult: (r: NlSqlWsPayload | null) => void;
  setInterpretationHint: (h: InterpretationHint | null) => void;
  setPreferDraftNl: (v: boolean) => void;
};

export function useAnalyticsHistory({
  activeId,
  nlConversationId,
  preferDraftNl,
  setNlConversationId,
  setQuestion,
  setMaxRowsStr,
  setResult,
  setInterpretationHint,
  setPreferDraftNl,
}: Args) {
  const [historyBusy, setHistoryBusy] = useState(true);
  const setActive = useAnalyticsChatStore((s) => s.setActive);
  const setEntriesFromServer = useAnalyticsChatStore((s) => s.setEntriesFromServer);
  const removeEntry = useAnalyticsChatStore((s) => s.removeEntry);
  const removeChatTitle = useAnalyticsChatTitlesStore((s) => s.removeTitle);
  const clearAllTitles = useAnalyticsChatTitlesStore((s) => s.clearAllTitles);

  const loadHistory = useCallback(async () => {
    setHistoryBusy(true);
    try {
      const data = await fetchAnalyticsHistory();
      setEntriesFromServer(data.items.map(historyItemToChatEntry));
    } catch {
      /* ignore */
    } finally {
      setHistoryBusy(false);
    }
  }, [setEntriesFromServer]);

  useEffect(() => {
    void loadHistory();
  }, [loadHistory]);

  const applyEntry = useCallback((e: AnalyticsChatEntry) => {
    setQuestion(e.question);
    setMaxRowsStr(e.maxRows != null ? String(e.maxRows) : "");
    setResult(e.result);
    const r = e.result as NlSqlWsPayload | null;
    setInterpretationHint(
      r?.interpretation ? interpretationToHint(r.interpretation) : null,
    );
  }, [setInterpretationHint, setMaxRowsStr, setQuestion, setResult]);

  const selectEntry = useCallback(
    (id: string) => {
      setPreferDraftNl(false);
      setActive(id);
      const e = useAnalyticsChatStore.getState().entries.find((x) => x.id === id);
      if (!e) return;
      if (e.kind === "nl_chat") {
        setNlConversationId(e.conversationId ?? e.id);
        setQuestion("");
        setMaxRowsStr("");
        setResult(null);
        setInterpretationHint(null);
        return;
      }
      setNlConversationId(null);
      applyEntry(e);
    },
    [
      applyEntry,
      setActive,
      setInterpretationHint,
      setMaxRowsStr,
      setNlConversationId,
      setPreferDraftNl,
      setQuestion,
      setResult,
    ],
  );

  useEffect(() => {
    if (historyBusy) return;
    if (preferDraftNl) return;
    if (nlConversationId != null) return;
    if (activeId != null) return;
    const firstNl = useAnalyticsChatStore
      .getState()
      .entries.find((e) => e.kind === "nl_chat");
    if (!firstNl) return;
    selectEntry(firstNl.id);
  }, [activeId, historyBusy, nlConversationId, preferDraftNl, selectEntry]);

  const deleteHistoryEntry = useCallback(
    async (rowId: string) => {
      try {
        const e = useAnalyticsChatStore.getState().entries.find((x) => x.id === rowId);
        if (e?.kind === "nl_chat") {
          await deleteNlChat(e.conversationId ?? rowId);
        } else {
          await deleteAnalyticsJob(rowId);
        }
        removeChatTitle(rowId);
        removeEntry(rowId);
        if (activeId === rowId) {
          setActive(null);
          setNlConversationId(null);
          setQuestion("");
          setMaxRowsStr("");
          setResult(null);
        }
      } catch {
        /* ignore */
      }
    },
    [
      activeId,
      removeChatTitle,
      removeEntry,
      setActive,
      setMaxRowsStr,
      setNlConversationId,
      setQuestion,
      setResult,
    ],
  );

  const clearAllHistoryEntries = useCallback(async () => {
    try {
      await deleteAllAnalyticsHistory();
      clearAllTitles();
      setEntriesFromServer([]);
      setNlConversationId(null);
      setActive(null);
      setPreferDraftNl(true);
      setQuestion("");
      setMaxRowsStr("");
      setResult(null);
      setInterpretationHint(null);
    } catch {
      /* ignore */
    }
  }, [
    clearAllTitles,
    setActive,
    setEntriesFromServer,
    setInterpretationHint,
    setMaxRowsStr,
    setNlConversationId,
    setPreferDraftNl,
    setQuestion,
    setResult,
  ]);

  return {
    historyBusy,
    loadHistory,
    selectEntry,
    deleteHistoryEntry,
    clearAllHistoryEntries,
  };
}
