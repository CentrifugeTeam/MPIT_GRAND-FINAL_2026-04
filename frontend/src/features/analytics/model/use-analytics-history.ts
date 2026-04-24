import { useCallback, useEffect, useState } from "react";

import {
  deleteAllAnalyticsHistory,
  deleteAnalyticsJob,
  deleteNlChat,
  fetchAnalyticsHistory,
  type AnalyticsHistoryItem,
} from "../api/analytics-api";
import type { NlSqlWsPayload } from "@/entities/analytics";
import { historyItemToChatEntry } from "../lib/history-mapper";
import {
  useAnalyticsChatStore,
  type AnalyticsChatEntry,
} from "./analytics-chat-store";
import { useAnalyticsChatTitlesStore } from "./analytics-chat-titles-store";
import {
  interpretationToHint,
  type InterpretationHint,
} from "../lib/interpretation-hint";

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
      // Совместные чаты (viewer) показываются только в блоке «Приглашённые/совместные» из fetchChatInvites.
      const mainOnly = data.items.filter((item: AnalyticsHistoryItem) => {
        if (item.entry_kind !== "nl_chat") return true;
        return item.access_role !== "viewer";
      });
      setEntriesFromServer(mainOnly.map(historyItemToChatEntry));
    } catch (err) {
      console.error("[analytics] Failed to load history:", err);
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
      if (!e) {
        // Совместный чат: id = conversation_id, в store нет (viewer не в общей истории).
        setNlConversationId(id);
        setQuestion("");
        setMaxRowsStr("");
        setResult(null);
        setInterpretationHint(null);
        return;
      }
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
        } else if (e?.kind === "sql_job") {
          await deleteAnalyticsJob(rowId);
        } else {
          // Строка только в «совместных» (viewer): conversation_id = rowId
          await deleteNlChat(rowId);
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
      } catch (err) {
        console.error("[analytics] Failed to delete history entry:", err);
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
    } catch (err) {
      console.error("[analytics] Failed to clear all history:", err);
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
