import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";

import {
  askAnalyticsAsync,
  deleteAllAnalyticsHistory,
  deleteAnalyticsJob,
  fetchAnalyticsHistory,
  rerunAnalyticsJobAsync,
} from "@/features/analytics/api/analytics-api";
import type { InterpretationHint } from "@/features/analytics/ui/analytics-panel/interpretation-banner";
import { interpretationToHint } from "@/features/analytics/ui/analytics-panel/interpretation-banner";
import { historyItemToChatEntry } from "@/features/analytics/lib/history-mapper";
import { watchNlSqlJobUntilResult } from "@/features/analytics/lib/watch-nl-sql-job";
import {
  useAnalyticsChatStore,
  type AnalyticsChatEntry,
} from "@/features/analytics/model/analytics-chat-store";
import { useAnalyticsChatTitlesStore } from "@/features/analytics/model/analytics-chat-titles-store";
import type { ChartPayloadShape, NlSqlWsPayload } from "@/entities/analytics/types";
import { useWsStore } from "@/shared/lib/ws-store";

import {
  ANALYTICS_STAGE_WEIGHT,
  type AnalyticsStageKey,
} from "../../lib/stage-weights";

export function useAnalyticsPanel() {
  const { t } = useTranslation();
  const entries = useAnalyticsChatStore((s) => s.entries);
  const activeId = useAnalyticsChatStore((s) => s.activeId);
  const upsertEntry = useAnalyticsChatStore((s) => s.upsertEntry);
  const updateEntry = useAnalyticsChatStore((s) => s.updateEntry);
  const setActive = useAnalyticsChatStore((s) => s.setActive);
  const setEntriesFromServer = useAnalyticsChatStore(
    (s) => s.setEntriesFromServer,
  );
  const removeEntry = useAnalyticsChatStore((s) => s.removeEntry);

  const titles = useAnalyticsChatTitlesStore((s) => s.titles);
  const setChatTitle = useAnalyticsChatTitlesStore((s) => s.setTitle);
  const removeChatTitle = useAnalyticsChatTitlesStore((s) => s.removeTitle);
  const clearAllTitles = useAnalyticsChatTitlesStore((s) => s.clearAllTitles);

  const [question, setQuestion] = useState("");
  const [maxRowsStr, setMaxRowsStr] = useState("");
  const [progress, setProgress] = useState(0);
  const [stageKey, setStageKey] = useState<AnalyticsStageKey>("idle");
  const [stageLabel, setStageLabel] = useState("");
  const [busy, setBusy] = useState(false);
  const [historyBusy, setHistoryBusy] = useState(false);
  const [editingRowId, setEditingRowId] = useState<string | null>(null);
  const [renameDraft, setRenameDraft] = useState("");
  const [renameFieldFocused, setRenameFieldFocused] = useState(false);
  const [result, setResult] = useState<NlSqlWsPayload | null>(null);
  const [interpretationHint, setInterpretationHint] = useState<InterpretationHint | null>(
    null,
  );
  const wsListenersCleanupRef = useRef<(() => void) | null>(null);
  const renameInputRef = useRef<HTMLInputElement>(null);
  const ensureWsConnected = useWsStore((s) => s.ensureConnected);
  const disconnectWs = useWsStore((s) => s.disconnect);

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

  useEffect(() => {
    if (editingRowId) {
      requestAnimationFrame(() => renameInputRef.current?.focus());
    }
  }, [editingRowId]);

  useEffect(() => {
    return () => {
      wsListenersCleanupRef.current?.();
      wsListenersCleanupRef.current = null;
      disconnectWs();
    };
  }, [disconnectWs]);

  const setStage = useCallback((key: AnalyticsStageKey, label?: string) => {
    setStageKey(key);
    setProgress(ANALYTICS_STAGE_WEIGHT[key]);
    if (label !== undefined) setStageLabel(label);
  }, []);

  const resetStageIdle = useCallback(() => {
    setStageKey("idle");
    setProgress(0);
    setStageLabel("");
  }, []);

  const startNewChat = useCallback(() => {
    setActive(null);
    setQuestion("");
    setMaxRowsStr("");
    setResult(null);
    setInterpretationHint(null);
    resetStageIdle();
  }, [resetStageIdle, setActive]);

  const startEditingRow = useCallback(
    (e: AnalyticsChatEntry) => {
      setEditingRowId(e.id);
      setRenameDraft(titles[e.id] ?? e.question);
    },
    [titles],
  );

  const cancelRename = useCallback(() => {
    setRenameFieldFocused(false);
    setEditingRowId(null);
    setRenameDraft("");
  }, []);

  const commitRename = useCallback(() => {
    if (!editingRowId) return;
    setChatTitle(editingRowId, renameDraft);
    setRenameFieldFocused(false);
    setEditingRowId(null);
    setRenameDraft("");
  }, [renameDraft, editingRowId, setChatTitle]);

  const confirmDeleteOne = useCallback(
    async (jobId: string) => {
      if (!window.confirm(t("home.analytics.deleteChatConfirmNative"))) return;
      try {
        await deleteAnalyticsJob(jobId);
        removeChatTitle(jobId);
        removeEntry(jobId);
        if (activeId === jobId) {
          setActive(null);
          setQuestion("");
          setMaxRowsStr("");
          setResult(null);
          resetStageIdle();
        }
      } catch {
        /* ignore */
      }
    },
    [
      activeId,
      removeChatTitle,
      removeEntry,
      resetStageIdle,
      setActive,
      t,
    ],
  );

  const confirmDeleteAll = useCallback(async () => {
    if (!window.confirm(t("home.analytics.deleteAllHistoryConfirmNative"))) return;
    try {
      await deleteAllAnalyticsHistory();
      clearAllTitles();
      setEntriesFromServer([]);
      startNewChat();
    } catch {
      /* ignore */
    }
  }, [clearAllTitles, setEntriesFromServer, startNewChat, t]);

  const cleanupWsListeners = useCallback(() => {
    wsListenersCleanupRef.current?.();
    wsListenersCleanupRef.current = null;
  }, []);

  const parseMaxRows = useCallback((): number | null => {
    const s = maxRowsStr.trim();
    if (!s) return null;
    const n = parseInt(s, 10);
    if (!Number.isFinite(n) || n < 1) return null;
    return Math.min(50_000_000, n);
  }, [maxRowsStr]);

  const applyEntry = useCallback((e: AnalyticsChatEntry) => {
    setQuestion(e.question);
    setMaxRowsStr(e.maxRows != null ? String(e.maxRows) : "");
    setResult(e.result);
    const r = e.result as NlSqlWsPayload | null;
    setInterpretationHint(
      r?.interpretation ? interpretationToHint(r.interpretation) : null,
    );
  }, []);

  const selectEntry = useCallback(
    (id: string) => {
      setActive(id);
      const e = useAnalyticsChatStore
        .getState()
        .entries.find((x) => x.id === id);
      if (e) applyEntry(e);
    },
    [applyEntry, setActive],
  );

  const run = useCallback(async () => {
    const q = question.trim();
    if (!q || busy) return;

    const maxRows = parseMaxRows();

    setBusy(true);
    setResult(null);
    setInterpretationHint(null);
    cleanupWsListeners();

    let jobIdForEntry: string | undefined;
    try {
      setStage("ask", t("home.analytics.stageQueue"));
      const data =
        activeId && useAnalyticsChatStore.getState().entries.some((e) => e.id === activeId)
          ? await rerunAnalyticsJobAsync(activeId, q, maxRows)
          : await askAnalyticsAsync(q, maxRows);
      const jobId = data.job_id;
      jobIdForEntry = jobId;
      setInterpretationHint({
        confidence: data.interpretation_confidence,
        warnings: data.interpretation_warnings ?? [],
        suggestions: data.interpretation_suggestions ?? [],
        glossaryTermsCount: data.glossary_matches?.length ?? 0,
      });
      upsertEntry({
        id: jobId,
        jobId,
        question: q,
        maxRows,
        createdAt:
          useAnalyticsChatStore
            .getState()
            .entries.find((e) => e.id === jobId)?.createdAt ?? Date.now(),
        result: null,
      });

      setStage("ws_connect", t("home.analytics.stageConnect"));

      await watchNlSqlJobUntilResult({
        jobId,
        ensureWsConnected,
        onBeforeWatchSent: () =>
          setStage("watch_sent", t("home.analytics.stageWatch")),
        onWatchAck: () => {
          setStage("ack", t("home.analytics.stageWaitWorker"));
        },
        onResult: (nlPayload) => {
          setStage("result", t("home.analytics.stageResult"));
          setResult(nlPayload);
          if (nlPayload.interpretation) {
            setInterpretationHint(interpretationToHint(nlPayload.interpretation));
          }
          updateEntry(jobId, { result: nlPayload });
          setStage("done", t("home.analytics.stageDone"));
        },
        timeoutMs: 120_000,
        getTimeoutError: () => new Error(t("home.analytics.timeout")),
        registerListenerCleanup: (fn) => {
          wsListenersCleanupRef.current = fn;
        },
      });
    } catch (e) {
      resetStageIdle();
      const errPayload = {
        job_id: jobIdForEntry ?? "",
        status: "error",
        error: e instanceof Error ? e.message : String(e),
        question: q,
      } as NlSqlWsPayload;
      setResult(errPayload);
      if (jobIdForEntry) {
        updateEntry(jobIdForEntry, { result: errPayload });
      }
    } finally {
      disconnectWs();
      setBusy(false);
    }
  }, [
    busy,
    cleanupWsListeners,
    disconnectWs,
    ensureWsConnected,
    parseMaxRows,
    question,
    activeId,
    resetStageIdle,
    setStage,
    t,
    updateEntry,
    upsertEntry,
  ]);

  const rerun = useCallback(() => {
    void run();
  }, [run]);

  const chartPayload = result?.chart_payload;
  const showChart = useMemo(() => {
    const cp = chartPayload as ChartPayloadShape | undefined;
    return Boolean(
      cp &&
        (cp.type === "bar" || cp.type === "line") &&
        (cp.labels?.length ?? 0) > 0 &&
        (cp.series?.length ?? 0) > 0,
    );
  }, [chartPayload]);

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
    confirmDeleteAll,
    startEditingRow,
    confirmDeleteOne,
    question,
    setQuestion,
    maxRowsStr,
    setMaxRowsStr,
    busy,
    stageKey,
    stageLabel,
    progress,
    run,
    rerun,
    result,
    showChart,
    chartPayload,
    interpretationHint,
  };
}
